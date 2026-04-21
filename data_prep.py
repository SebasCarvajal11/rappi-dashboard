import pandas as pd
import glob
import os

def procesar_csvs(carpeta_origen, archivo_destino):
    archivos = glob.glob(os.path.join(carpeta_origen, "*.csv"))
    dataframes =[]

    print(f"Encontrados {len(archivos)} archivos. Procesando...")

    for archivo in archivos:
        try:
            # Leer el CSV
            df = pd.read_csv(archivo)
            
            # Las primeras 4 columnas son metadatos, el resto son fechas
            columnas_metadatos = df.columns[:4].tolist()
            
            # Usamos pd.melt para pasar de formato "ancho" a "largo"
            df_largo = pd.melt(df, 
                               id_vars=columnas_metadatos, 
                               var_name="Fecha_String", 
                               value_name="Tiendas_Disponibles")
            
            # Limpiar el string de la fecha (quitar 'GMT-0500...') para poder convertirlo a datetime
            df_largo['Fecha_String'] = df_largo['Fecha_String'].str.split(' GMT').str[0]
            
            # Convertir a formato de fecha real
            df_largo['Fecha'] = pd.to_datetime(df_largo['Fecha_String'], format='%a %b %d %Y %H:%M:%S')
            
            # Quedarnos solo con lo que importa y ordenarlo
            df_final = df_largo[['Fecha', 'Tiendas_Disponibles']].copy()
            dataframes.append(df_final)
        except Exception as e:
            print(f"Error procesando {archivo}: {e}")

    # Validar que realmente haya algo que unir antes de intentar hacerlo
    if len(dataframes) == 0:
        print("Error: No se encontraron DataFrames para unir. Revisa la ruta de la carpeta.")
        return

    # Unir todos los dataframes y ordenar por fecha
    df_master = pd.concat(dataframes, ignore_index=True)
    df_master = df_master.sort_values('Fecha').reset_index(drop=True)
    
    # Guardar en un solo CSV
    df_master.to_csv(archivo_destino, index=False)
    print(f"¡Listo! Archivo guardado en {archivo_destino} con {len(df_master)} registros.")

# Ejecutar la función con el nombre correcto de tu carpeta
procesar_csvs('Archivo/', 'master_data.csv')