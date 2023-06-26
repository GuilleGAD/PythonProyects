import argparse
from tsvToCsv import Converter

def Args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--tocsv',type=str,help="Choose the input file to convert to csv")
    parser.add_argument('--out',type=str,help="Choose a name for the output file (optional)")
    parser.add_argument('--delim',type=str,help="Choose a specific delimiter for your output (optional)")
    args = parser.parse_args()

    try:
        input = args.tocsv
        if args.out:
            output = args.out
            if args.delim:
                delim = args.delim
                Converter(args.tocsv).convert_to_csv(args.out,args.delim)
            else:
                Converter(args.tocsv).convert_to_csv(args.out)
        else:
            Converter(args.tocsv).convert_to_csv()
    except:
        raise Exception("You need to write the input file")

    
if __name__ == '__main__':
    Args()