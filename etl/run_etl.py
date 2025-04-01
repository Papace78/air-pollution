from tqdm import tqdm

from extract import extract_data
from transform import transform_data
from load import load_data

def run():
    extracted_data = extract_data()
    transformed_data = transform_data(extracted_data)

    '''for table, df in tqdm(transformed_data.items(), desc ="Loading data", unit = "table"):
        load_data(table, df)'''

    print("✅ Data loaded successfully!")

if __name__=='__main__':
    run()
