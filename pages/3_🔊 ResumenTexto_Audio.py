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
from gtts import gTTS
from io import BytesIO
import nltk
from nltk.tokenize import sent_tokenize
nltk.download('punkt')


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
def summarize_text(text, max_sentences=3):
    sentences = sent_tokenize(text)
    summary = ' '.join(sentences[:max_sentences])
    return summary

def text_to_speech(text, language='es'):
    tts = gTTS(text=text, lang=language, slow=False)
    audio = BytesIO()
    tts.write_to_fp(audio)
    return audio


def main():
    st.set_page_config(page_title="Texto a Audio", page_icon="🔊")
    st.sidebar.header("Texto a audio")
    st.title("DOF TO AUDIO")
    st.header(':blue[Resúmenes de texto y audio]', divider='blue')
    st.subheader(':grey[ Resume las publicaciones del Diario OFicial de la Federación y transfórmalas, con IA,  a audio y más]', divider='blue')
    fecha_seleccionada = st.date_input("Selecciona una fecha", datetime.date.today())
    dependencia = 'Todos'
    # Fetch data
    fecha_formateada = fecha_seleccionada.strftime('%d-%m-%Y')
    url = f"https://sidofqa.segob.gob.mx/dof/sidof/notas/{fecha_formateada}"
    if 'df_extracted_data' not in st.session_state or st.button('Consultar DOF'):
        st.session_state.df_extracted_data = fetch_and_prepare_data(url)
        add_text_to_df(st.session_state.df_extracted_data)             
        if len(st.session_state.df_extracted_data) > 0:
            #st.write(f"Total de publicaciones en el DOF para {fecha_seleccionada.strftime('%Y-%m-%d')}: {len(st.session_state.df_extracted_data)}")
            st.markdown(f"<span style='color: red;'>Total de publicaciones en el DOF para {fecha_seleccionada.strftime('%Y-%m-%d')}: {len(st.session_state.df_extracted_data)}</span>", unsafe_allow_html=True)
        else:
            st.error("No hay publicaciones para la fecha seleccionada, por favor seleccione otra fecha")
        # Muestra el selectbox de dependencia independientemente de la carga de datos inicial
    if 'df_extracted_data' in st.session_state and len(st.session_state.df_extracted_data) > 0:
        dependencia = st.selectbox("Selecciona una DEPENDENCIA:", options=['Todos'] + list(st.session_state.df_extracted_data['DEPENDENCIA'].unique()))

        #total_publicaciones = len(st.session_state.df_extracted_data)
        
        #if total_publicaciones > 0:  # Asegura que hay publicaciones para mostrar
        #    dependencia = st.selectbox("Selecciona una DEPENDENCIA:", options=['Todos'] + list(st.session_state.df_extracted_data['DEPENDENCIA'].unique()))
        #else:
        #    st.error("No hay publicaciones para la fecha seleccionada, por favor seleccione otra fecha")
    

        #dependencia = st.selectbox("Selecciona una DEPENDENCIA:", options=['Todos'] + list(st.session_state.df_extracted_data['DEPENDENCIA'].unique()))

    #else:
    #    st.error("No hay publicaciones para la fecha seleccionada, por favor seleccione otra fecha")
    # st.write(st.session_state.df_extracted_data)
    # Select DEPENDENCIA
        # Permitir al usuario seleccionar una DEPENDENCIA
    
    if dependencia != 'Todos':
        # Filtrar DataFrame basado en la DEPENDENCIA seleccionada
        filtered_df = st.session_state.df_extracted_data[st.session_state.df_extracted_data['DEPENDENCIA'] == dependencia]
    else:
        filtered_df = st.session_state.df_extracted_data if 'df_extracted_data' in st.session_state else pd.DataFrame()

    # Permitir al usuario seleccionar uno o varios TÍTULOS de la dependencia seleccionada
    selected_titulos = st.multiselect("Por favor selecciona uno o más TÍTULOS:", options=filtered_df['TITULO'].unique())

    if selected_titulos:
        # Mostrar TEXTONOTA de los títulos seleccionados
        for titulo in selected_titulos:
            selected_textonota = filtered_df[filtered_df['TITULO'] == titulo]['TEXTONOTA'].iloc[0]
            preview_text = selected_textonota[:500] 
            #num_parrafos_mostrar = 2
            #resumen_texto = '\n\n'.join(parrafos[:num_parrafos_mostrar])
            st.write(f"Texto de '{titulo}':")
            st.write(preview_text + "...")
            #st.write(resumen_texto)
            #total_parrafos = len(parrafos)
            #st.write(f"Total de párrafos en la nota: {total_parrafos}")
    if st.button("Generar Resumen y Audio"):
    # Asume selected_textonota es el texto seleccionado por el usuario
      summary = summarize_text(selected_textonota)
    
    # Mostrar el resumen
      st.write("Resumen del Texto Seleccionado:")
      st.write(summary)
    
    # Convertir el resumen a audio
      audio = text_to_speech(summary)
    
    # Mostrar el widget de audio en Streamlit para reproducir el audio generado
      st.audio(audio.getvalue(), format='audio/mp3')
    else:
        st.error("Por favor selecciona al menos un título para generar el resumen y audio.")


if __name__ == "__main__":
    main()
