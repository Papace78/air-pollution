from extract import extract
from transform import transform

if __name__=='__main__':
    data = extract()
    df = transform(data)
    __import__('IPython').embed()
