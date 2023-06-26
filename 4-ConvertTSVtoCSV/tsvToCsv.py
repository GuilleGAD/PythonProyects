import codecs

class Converter:
    
    def __init__(self, input_file) -> None:
        self.input_file = input_file
        self.row = str()
        self.total_colums = int()
        self.delimiter = str()
        self.lines_to_write = list()
        self.output_file = None
        
    def count_colums(self, file) -> None:
        """cuenta el numero de columnas del archivo

        Args:
            file (_type_): archivo de entrada
        """
        self.total_colums = len(file.readline().split('\t'))
        file.seek(0)
        
    def clean_row(self, line:str) -> str:
        """limpita las columnas antes de la inserción en la fila

        Args:
            line (_type_): linea de entrada

        Returns:
            str: linea limpia de salida
        """
        last_line = False
        if not '\n' in line:
            last_line = True

        rows = line.split(self.delimiter)
        final_line = str()
        for i in range(0, self.total_colums):
            if i == self.total_colums - 1 and not last_line:
                final_line += f'{rows[i].rstrip().lstrip()}\n'
            elif i == self.total_colums - 1 and last_line:
                final_line += f'{rows[i].rstrip().lstrip()}'
            else:
                rows[i] = rows[i].replace('\n','')
                final_line += f'{rows[i].rstrip().lstrip()}{self.delimiter}'
                
        return final_line
    
    def write_in_csv(self) -> None:
        """Escribe una linea en el archivo de salida

        Args:
            line (_type_): linea de entrada
            file (_type_): archivo en donde se escribirá la linea
        """
        with open(self.output_file,'a') as file:
            for line in self.lines_to_write:
                file.write(f'{line}')
        self.lines_to_write.clear()
                
    def add_lines_to_write(self, line) -> None:
        self.lines_to_write.append(line)
        if len(self.lines_to_write) == 200: 
            self.write_in_csv()
                        
    
    def convert_to_csv(self, output_file="output.csv", delimiter=",") -> None:
        """Funcion main para leer el archivo de entrada y escribir esos datos
        en el archivo csv de salida

        Args:
            output_file (_type_): archivo csv de salida
            delimiter (_type_): delimitador del output (,)
        """
        
        self.delimiter = delimiter
        self.output_file = output_file
        
        with codecs.open(self.input_file, "r", encoding="utf-8") as file:
            self.count_colums(file)
            for line in file:
                if len(line.rstrip().split('\t')) == self.total_colums:
                    #si el numero de columnas es el correcto
                    line = self.clean_row(line.replace('\t',self.delimiter))
                    self.add_lines_to_write(line)
                else:
                    #sino, esta será agregada en la siguiente linea
                    self.row += line.replace('\t',self.delimiter)
                    
                if len(self.row.split(self.delimiter)) == self.total_colums:
                    self.row = self.clean_row(self.row)
                    self.add_lines_to_write(self.row)
                    self.row = str()
                    
        self.write_in_csv()
                    
        print("Archivo convertido exitosamente en CSV")



"""             
if __name__ == '__main__':
    Converter("1-sample.tsv").convert_to_csv("salida.csv")
"""