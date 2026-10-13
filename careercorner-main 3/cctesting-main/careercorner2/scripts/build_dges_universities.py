import pandas as pd
import requests
from io import BytesIO
from pathlib import Path

DGES_RESULTS_XLS = "https://dges.gov.pt/coloc/2025/cna25_1f_resultados.xls"

OUT_CSV = Path("data/universities_2025_1f.csv")
OUT_CSV.parent.mkdir(parents=True, exist_ok=True)


def download_results_xls(url: str) -> pd.DataFrame:
    """Downloading DGES results Excel file"""
    print(f"Downloading DGES data from {url}...")
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    
    # trying different skiprows to find correct header row
    for skip in [0, 1, 2, 3, 4]:
        try:
            df = pd.read_excel(BytesIO(resp.content), engine='xlrd', skiprows=skip)
            
            has_institution = any('institu' in str(col).lower() for col in df.columns)
            has_course = any('curso' in str(col).lower() for col in df.columns)
            
            if has_institution and has_course:
                print(f"Found valid headers at row {skip}")
                return df
        except Exception as e:
            continue
    
    raise ValueError("Could not find valid column headers")


def normalize_results(df: pd.DataFrame) -> pd.DataFrame:
    """Cleaning and normalising DGES data"""
    
    #trying to detect correct column names
    col_mapping = {}
    for col in df.columns:
        col_lower = str(col).lower()
        if 'institui' in col_lower and 'nome' in col_lower:
            col_mapping['institution_name'] = col
        elif 'curso' in col_lower and 'nome' in col_lower:
            col_mapping['course_name'] = col
        elif 'institui' in col_lower and ('cod' in col_lower or 'código' in col_lower):
            col_mapping['inst_code'] = col
        elif 'curso' in col_lower and ('cod' in col_lower or 'código' in col_lower):
            col_mapping['course_code'] = col
        elif 'grau' in col_lower:
            col_mapping['degree_type'] = col
        elif 'vaga' in col_lower and 'inicial' in col_lower:
            col_mapping['vacancies'] = col
        elif col == 'Colocados ' or (col_lower == 'colocados' and 'sem' not in col_lower and 'desemp' not in col_lower):
            col_mapping['placed'] = col
        elif 'nota' in col_lower and 'últ' in col_lower and 'geral' in col_lower:
            col_mapping['last_grade'] = col
    
    print("detected column mapping:", col_mapping)
    
    if not col_mapping:
        raise ValueError("Could not detect any valid columns. File structure may have changed.")
    
    df = df.rename(columns={v: k for k, v in col_mapping.items()})
    
    if 'institution_name' in df.columns:
        df['institution_name'] = df['institution_name'].astype(str).str.strip()
        df = df[df['institution_name'] != 'nan'].copy()
        df = df[df['institution_name'].str.len() > 3].copy()
    else:
        raise ValueError("Could not find institution_name column")
    
    if 'course_name' in df.columns:
        df['course_name'] = df['course_name'].astype(str).str.strip()
        df = df[df['course_name'] != 'nan'].copy()
    else:
        raise ValueError("Could not find course_name column")
    
    if 'last_grade' in df.columns:
        df['last_grade'] = pd.to_numeric(df['last_grade'], errors='coerce')
    
    if 'vacancies' in df.columns:
        df['vacancies'] = pd.to_numeric(df['vacancies'], errors='coerce')
    if 'placed' in df.columns:
        df['placed'] = pd.to_numeric(df['placed'], errors='coerce')
    
    df['region'] = df['institution_name'].apply(infer_region_from_name)
    df['type'] = df['institution_name'].apply(infer_type_from_name)
    
    keep_cols = [col for col in [
        'inst_code', 'course_code', 'institution_name', 'course_name',
        'degree_type', 'vacancies', 'placed', 'last_grade', 'region', 'type'
    ] if col in df.columns]
    
    return df[keep_cols]


def infer_region_from_name(name: str) -> str:
    """Infer region from institution name"""
    n = name.lower()
    if 'lisboa' in n or 'lisbon' in n:
        return "Lisbon"
    if 'porto' in n:
        return "Porto"
    if 'coimbra' in n:
        return "Coimbra"
    if 'braga' in n or 'minho' in n:
        return "Braga"
    if 'faro' in n or 'algarve' in n:
        return "Faro"
    if 'évora' in n or 'evora' in n:
        return "Évora"
    if 'aveiro' in n:
        return "Aveiro"
    if 'beira' in n:
        return "Covilhã"
    if 'setúbal' in n or 'setubal' in n:
        return "Setúbal"
    if 'leiria' in n:
        return "Leiria"
    return "Other"


def infer_type_from_name(name: str) -> str:
    """Infering institution type from name"""
    n = name.lower()
    if 'politécnico' in n or 'politecnico' in n:
        return "Polytechnic"
    if 'privad' in n or 'católica' in n or 'catolica' in n or 'lusíada' in n or 'lusofona' in n or 'lusófona' in n:
        return "Private"
    return "Public"


def add_coordinates(df: pd.DataFrame) -> pd.DataFrame:
    """Adding GPS coordinates for major institutions"""
    
    # manual mapping for the main Portuguese universities
    coords_map = {
        "Universidade de Lisboa": (38.7485, -9.1604),
        "Universidade do Porto": (41.1523, -8.6360),
        "Universidade de Coimbra": (40.2070, -8.4240),
        "Instituto Superior Técnico": (38.7369, -9.1395),
        "Universidade Nova de Lisboa": (38.7376, -9.1545),
        "ISCTE": (38.7482, -9.1484),
        "Universidade do Minho": (41.5607, -8.3970),
        "Universidade de Aveiro": (40.6306, -8.6590),
        "Universidade de Évora": (38.5729, -7.9081),
        "Universidade do Algarve": (37.0194, -7.9322),
        "Instituto Politécnico de Lisboa": (38.7223, -9.1393),
        "Instituto Politécnico do Porto": (41.1784, -8.6068),
        "Instituto Politécnico de Coimbra": (40.2033, -8.4103),
        "Instituto Politécnico de Leiria": (39.7436, -8.8070),
        "Universidade Católica Portuguesa": (38.7304, -9.1563),
        "Universidade da Beira Interior": (40.2773, -7.5060),
        "Instituto Politécnico de Setúbal": (38.5244, -8.8882),
        "Instituto Politécnico de Bragança": (41.8057, -6.7571),
        "Instituto Politécnico de Viana do Castelo": (41.6938, -8.8341),
    }
    
    df['lat'] = None
    df['lon'] = None
    
    for inst, (lat, lon) in coords_map.items():
        mask = df['institution_name'].str.contains(inst, case=False, na=False, regex=False)
        df.loc[mask, 'lat'] = lat
        df.loc[mask, 'lon'] = lon
    
    coords_count = df['lat'].notna().sum()
    print(f"Coordinates added for {coords_count}/{len(df)} entries ({coords_count/len(df)*100:.1f}%)")
    
    return df


def main():
    """Main ETL pipeline"""
    try:
        df_raw = download_results_xls(DGES_RESULTS_XLS)
        df = normalize_results(df_raw)
        df = add_coordinates(df)
        
        df.to_csv(OUT_CSV, index=False)
        print(f"\nSuccess. Saved {len(df)} rows to {OUT_CSV}")
        print(f"\nSample data:")
        print(df.head(3).to_string())
        print(f"\nColumns: {df.columns.tolist()}")
        print(f"\nRegions: {df['region'].value_counts().to_dict()}")
        print(f"Types: {df['type'].value_counts().to_dict()}")
        
        if 'last_grade' in df.columns:
            valid_grades = df['last_grade'].dropna()
            if len(valid_grades) > 0:
                print(f"\nGrade range: {valid_grades.min():.1f} - {valid_grades.max():.1f}")
                print(f"Courses with grade data: {len(valid_grades)}/{len(df)} ({len(valid_grades)/len(df)*100:.1f}%)")
            else:
                print("\n⚠︎ Warning:No valid grade data found")
        else:
            print("\n⚠︎ Warning:'last_grade' column not found in data")
        
    except Exception as e:
        print(f"\n⃠ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
