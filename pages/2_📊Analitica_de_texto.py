import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import nltk
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from fpdf import FPDF
import json
from nltk.corpus import stopwords
import base64
from PIL import Image
import datetime

#from openai import OpenAI
#import streamlit as st

# Ensure you have downloaded the stopwords
nltk.download('stopwords')

# Set of Spanish stopwords
stopwords_es = set(stopwords.words('spanish'))

# Function to remove stopwords from a document
def eliminar_stopwords(documento):
    palabras = documento.split()
    palabras_filtradas = [palabra for palabra in palabras if palabra.lower() not in stopwords_es]
    return ' '.join(palabras_filtradas)

# Function to fetch and prepare data
def fetch_and_prepare_data(url):
    response = requests.get(url).text
    data = json.loads(response)
    extracted_info = []
    for section in data:
        if isinstance(data[section], list):
            for item in data[section]:
                if 'codNota' in item and 'nombreCodOrgaUno' in item and 'codOrgaDos' in item:
                    extracted_info.append({
                        'CÓDIGODELANOTA': item['codNota'],
                        'PODER/ORGANOQPUBLICA': item['nombreCodOrgaUno'],
                        'DEPENDENCIA': item['codOrgaDos'],
                        'TITULO': '',  # Placeholder, will be filled in the next function
                        'TEXTONOTA': ''  # Placeholder, will be filled in the next function
                    })
    return pd.DataFrame(extracted_info)                
    #df = pd.DataFrame(extracted_info)
    #return add_text_to_df(df)
    return df
# Function to add TITULO and TEXTONOTA to DataFrame
def add_text_to_df(df):
    for index, row in df.iterrows():
        url = f"https://sidofqa.segob.gob.mx/dof/sidof/notas/nota/{row['CÓDIGODELANOTA']}"
        response = requests.get(url).text
        note_data = json.loads(response)  
        if 'Nota' in note_data:
            df.at[index, 'TITULO'] = note_data['Nota'].get('titulo', '')
            if 'cadenaContenido' in note_data['Nota']:
                html_content = note_data['Nota']['cadenaContenido']
                soup = BeautifulSoup(html_content, 'html.parser')
                df.at[index, 'TEXTONOTA'] = soup.body.get_text(separator=' ', strip=True) if soup.body else "Contenido no disponible"
                
#    return df
def visualize_term_frequencies(text):
    # Preprocesamiento básico: dividir el texto en tokens y contar frecuencias
    tokens = text.split()
    
    #Opcional: filtrar stopwords
    tokens = [token for token in tokens if token.lower() not in stopwords_es]
    
    term_freq = pd.Series(tokens).value_counts().head(10)  # Top 10 términos más frecuentes

    # Crear y configurar el gráfico de barras
    fig, ax = plt.subplots()
    term_freq.plot(kind='bar', ax=ax, color='skyblue')
    ax.set_xlabel('Término')
    ax.set_ylabel('Frecuencia')
    ax.set_title('Términos más frecuentes')
    
    return fig
# Streamlit App
def main():
    st.set_page_config(page_title="Analítica de texto", page_icon="📊")
    st.sidebar.header("Analítica de texto")
    st.title("DOF TO VIZ")
    st.header(':blue[Analítica de texto con el DOF]', divider='blue')
    st.subheader(':grey[Consulta el Diario OFicial de la Federación y obten analítica de texto, audio y más]', divider='blue')
    fecha_seleccionada = st.date_input("Selecciona una fecha", datetime.date.today())

    # Fetch data
    fecha_formateada = fecha_seleccionada.strftime('%d-%m-%Y')
    url = f"https://sidofqa.segob.gob.mx/dof/sidof/notas/{fecha_formateada}"
    #if 'df_extracted_data' not in st.session_state or st.button('Consultar DOF'):
    #    st.session_state.df_extracted_data = fetch_and_prepare_data(url)
    #    add_text_to_df(st.session_state.df_extracted_data)

    #if 'df_extracted_data' not in st.session_state:
    #    st.session_state.df_extracted_data = fetch_and_prepare_data(url)
    #    add_text_to_df(st.session_state.df_extracted_data)  # Llamada a la función para añadir texto y título
    if 'df_extracted_data' not in st.session_state or st.button('Consultar DOF'):
        st.session_state.df_extracted_data = fetch_and_prepare_data(url)
        add_text_to_df(st.session_state.df_extracted_data)
        fecha_formateada = fecha_seleccionada.strftime('%Y-%m-%d')
        total_publicaciones = len(st.session_state.df_extracted_data)
        st.markdown(f'<span style="color: red;">Total de publicaciones en el DOF para {fecha_formateada}: {total_publicaciones}</span>', unsafe_allow_html=True)
        #st.write( :blue[f"Total de publicaciones en el DOF para {fecha_formateada}: {total_publicaciones}")
    else:
        if len(st.session_state.df_extracted_data) == 0:
            st.error("No hay publicaciones para la fecha seleccionada, por favor seleccione otra fecha")    
        #st.write(st.session_state.df_extracted_data)
    # Select DEPENDENCIA
        # Permitir al usuario seleccionar una DEPENDENCIA
    st.write("A continuación se muestran las Dependencias que publicaron en el DOF en la fecha seleccionada")    
    dependencia = st.selectbox(" Por favor selecciona una DEPENDENCIA para ver los TÍTULOS de sus publicaciones:", options=['Todos'] + list(st.session_state.df_extracted_data['DEPENDENCIA'].unique()))

    if dependencia != 'Todos':
        # Filtrar DataFrame basado en la DEPENDENCIA seleccionada
        filtered_df = st.session_state.df_extracted_data[st.session_state.df_extracted_data['DEPENDENCIA'] == dependencia]
    else:
        filtered_df = st.session_state.df_extracted_data

    # Permitir al usuario seleccionar uno o varios TÍTULOS de la dependencia seleccionada
    selected_titulos = st.multiselect("Por favor selecciona uno o más TÍTULOS:", options=filtered_df['TITULO'].unique())

    if selected_titulos:
        # Mostrar TEXTONOTA de los títulos seleccionados
        for titulo in selected_titulos:
            selected_textonota = filtered_df[filtered_df['TITULO'] == titulo]['TEXTONOTA'].iloc[0]
            preview_text = selected_textonota[:1000]
            st.write(f"Texto de '{titulo}':")
            st.write(preview_text + "...")
    
    # Select TITULO
    #titulo = st.selectbox("Selecciona un TITULO:", options=filtered_df['TITULO'])

    # Find selected TEXTONOTA
    #selected_textonota = filtered_df[filtered_df['TITULO'] == titulo]['TEXTONOTA'].iloc[0]

    # Button to generate visualization
    if st.button("Visualizar TITULO (S) seleccionados"):
        text = eliminar_stopwords(selected_textonota)
        wordcloud = WordCloud(width=800, height=400, background_color ='white', stopwords=stopwords_es).generate(text)
        plt.figure(figsize=(10, 5))
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis("off")
        plt.show()
        st.pyplot(plt)

    #if selected_titulos:
        combined_text = " ".join(filtered_df[filtered_df['TITULO'].isin(selected_titulos)]['TEXTONOTA'])
        fig = visualize_term_frequencies(combined_text)
        st.pyplot(fig)  # Mostrar el gráfico en la aplicación Streamlit

# Run the app
if __name__ == "__main__":
    main()
