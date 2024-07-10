import streamlit as st
import pandas as pd
import json
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize
from openai import OpenAI
import ast
import nltk

nltk.download('punkt')

# Asegúrate de configurar tus claves de API de OpenAI en `st.secrets`
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])


#def get_embedding(text, model="text-embedding-ada-002"):
#    text = text.replace("\n", " ")
#    response = client.embeddings.create(input=[text], model=model)

#    return response['data'][0]['embedding']
# Función para obtener embeddings de texto utilizando un modelo de OpenAI.
def get_embedding(text, model="text-embedding-ada-002"):
    text = text.replace("\n", " ")# Reemplaza saltos de línea por espacios para evitar errores en el procesamiento.
    return client.embeddings.create(input=[text], model=model).data[0].embedding # Llama a la API de OpenAI para obtener el embedding del texto, retorna el embedding
# Función para calcular la distancia cosina entre dos vectores.
def cosine_distance(v1, v2):
    dot_product = sum(a*b for a, b in zip(v1, v2))
    magnitude_v1 = sum(a*a for a in v1) ** 0.5
    magnitude_v2 = sum(a*a for a in v2) ** 0.5
    if magnitude_v1 == 0 or magnitude_v2 == 0:
        return 1
    return 1 - dot_product / (magnitude_v1 * magnitude_v2)
# Función para crear un contexto basado en la pregunta del usuario, seleccionando trámites relevantes.
def create_context(question, df):# Obtiene el embedding de la pregunta.
    q_embedding = get_embedding(question)
    df['distance'] = df['embedding'].apply(lambda emb: cosine_distance(q_embedding, emb))
    sorted_df = df.sort_values('distance')# Ordena los trámites por su distancia (relevancia).
    relevant_tramites = sorted_df['Trámite'].unique()[:5]# Selecciona los 5 trámites más relevantes.
    return relevant_tramites




#def calculate_cosine_distance(emb1, emb2):
#    return spatial.distance.cosine(emb1, emb2)
def build_context_for_selected_tramite(df, tramite_elegido, max_len=3000):
    # Selecciona todas las entradas para el trámite elegido.
    df_filtrado = df[df['Trámite'] == tramite_elegido]
    context = ""
    total_len = 0
    for _, row in df_filtrado.iterrows():
        text_len = len(row['Combined'].split())
        if total_len + text_len > max_len:
            break
        context += row['Combined'] + "\n\n"
        total_len += text_len
    return context

#def create_context(question, df):
 #   q_embedding = get_embedding(question)
 #   df['distance'] = df['embedding'].apply(lambda emb: calculate_cosine_distance(q_embedding, emb))
 #   sorted_df = df.sort_values('distance')
 #   relevant_tramites = sorted_df['Trámite'].unique()[:3]
 #   return relevant_tramites
# Función para construir el contexto para un trámite seleccionado.
#def build_context_for_selected_tramite(df, tramite_elegido, max_len=3000, pregunta=None):
#    Filtra el DataFrame por trámite seleccionado, y opcionalmente por pregunta.
#    if pregunta:
#        df_filtrado = df[(df['Trámite'] == tramite_elegido) #& (df['Pregunta_Completa'] == pregunta)]
#    else:
#        df_filtrado = df[df['Trámite'] == tramite_elegido]
#    context = "" # Inicializa el contexto como un string vacío.
#    total_len = 0 # Inicializa el contador de longitud total del contexto.
#    for _, row in df_filtrado.iterrows():
#        text_len = len(row['Combined'].split()) # Calcula la longitud del texto actual.
#        if total_len + text_len > max_len: # Verifica si agregar este texto superaría el límite de longitud.
#            break
#        context += row['Combined'] + "\n\n" # Agrega el texto al contexto.
#        total_len += text_len # Retorna el contexto construido.
#    return context


# Función para generar respuestas a preguntas utilizando el contexto y el modelo de OpenAI.

def answer_questions(questions, context="", model="gpt-4", max_tokens=500):
    responses = [] # Inicializa una lista para almacenar las respuestas.
    # Itera sobre cada pregunta para generar una respuesta.
    for question in questions:
        try:
            # Genera una respuesta utilizando el modelo de OpenAI y el contexto proporcionado.
            response = client.chat.completions.create( 
                model=model,
                messages=[
                    {"role": "system", "content": "Eres un especialista en temas fiscales en México. Vas a responder consultas sobre los trámites del anexo 1-A de la Resolución Miscelánea Fiscal 2023 de México responde de forma amable, si la respuesta consiste en múltiples pasos o documentos responde haciendo una lista de la información. Si el usuario ingreso texto en  Ingresa tu pregunta o describe el trámite que te interesa, responde basado en todos los embeddings del trámite seleccionado"},
                    {"role": "user", "content": f"Context: {context}\n\n---\n\nQuestion: {question}\nAnswer:"}
                ],
                temperature=0.5,
                max_tokens=max_tokens,
                top_p=1.0,
                frequency_penalty=0.0,
                presence_penalty=0.0,
            )
            # Extrae la respuesta generada y la añade a la lista de respuestas.
            text_response = response.choices[0].message.content
            responses.append(text_response.strip())
        except Exception as e:
            print(e)
            responses.append("")
    return responses

def main():
    st.title("Asistente para Trámites Fiscales")

    df = pd.read_csv("./data/TODOStramitesembdf_modificadoVF.csv")

    # df2 = pd.read_csv("./data/tramitespreguntasEMBVFfundamentoVF.csv")
     #df['Pregunta_Completa'] = df2['Pregunta_Completa']
     #df['Fundamento jurídico'] = df2['Fundamento jurídico']

     #df['embedding'] = df['embedding'].astype(str).apply(ast.literal_eval)
    df['embedding'] = df['embedding'].astype(str).apply(eval)
    #df['embedding'] = df['embedding'].apply(lambda emb: json.loads(emb) if isinstance(emb, str) else emb)

    busqueda_opcion = st.radio("¿Cómo deseas buscar?", ('Por Fundamento Jurídico', 'Describir Trámite o Pregunta'))

    if busqueda_opcion == 'Por Fundamento Jurídico':
        df_filterderogado = df[~df['Fundamento jurídico'].str.contains("Trámite derogado", na=False)]
        fundamentos_legales = df_filterderogado['Fundamento jurídico'].dropna().unique()
        fundamento_seleccionado = st.selectbox("Selecciona el fundamento legal de tu interés:", [''] + list(fundamentos_legales))
        pass

        if fundamento_seleccionado:
            tramites_asociados = df_filterderogado[df_filterderogado['Fundamento jurídico'] == fundamento_seleccionado]['Trámite'].unique()
            tramite_seleccionado = st.selectbox("Selecciona el trámite asociado:", [''] + list(tramites_asociados))

    else:
        question = st.text_input("Ingresa tu pregunta o describe el trámite que te interesa:")
        if question:
            relevant_tramites = create_context(question, df)
            tramite_elegido = st.selectbox("Trámites sugeridos basados en tu descripción:", relevant_tramites)

    if 'tramite_seleccionado' in locals() or 'tramite_elegido' in locals():
        selected_tramite = tramite_seleccionado if 'tramite_seleccionado' in locals() else tramite_elegido
        preguntas_df = df[df['Trámite'] == selected_tramite]
        preguntas = preguntas_df['Pregunta_Completa'].dropna().unique()
        
        pregunta_seleccionada = st.selectbox("Selecciona una pregunta de tu interés:", [''] + list(preguntas), key='pregunta_seleccionada')        
        pregunta_seleccionada_index = -1 if pregunta_seleccionada == '' else preguntas.tolist().index(pregunta_seleccionada)
    #if 'tramite_seleccionado' in locals() or 'tramite_elegido' in locals():
    #    selected_tramite = tramite_seleccionado if 'tramite_seleccionado' in locals() else tramite_elegido
    #    preguntas_df = df[df['Trámite'] == selected_tramite]
    #    preguntas = preguntas_df['Pregunta_Completa'].dropna().unique()
    #    pregunta_seleccionada = st.selectbox("Selecciona una pregunta de tu interés:", [''] + list(preguntas))
  
        nueva_pregunta = "" #st.text_input("Ingresa tu nueva pregunta aquí:")
        if pregunta_seleccionada_index == -1:
            nueva_pregunta = st.text_input("Ingresa tu nueva pregunta aquí:", key='nueva_pregunta')
            #nueva_pregunta = st.text_input("Ingresa tu nueva pregunta aquí:", key='nueva_pregunta')

        if st.button("Obtener Respuesta"):
            pregunta_final = nueva_pregunta if nueva_pregunta else pregunta_seleccionada
            if pregunta_final:
                context = build_context_for_selected_tramite(df, selected_tramite)
                response = answer_questions([pregunta_final], context=context)[0]
                st.text_area("Respuesta:", value=response, height=150)
        #if st.button("Obtener Respuesta"):
        #    pregunta_final = nueva_pregunta if nueva_pregunta else pregunta_seleccionada
        #    if pregunta_final:
        #        # Ahora se construye el contexto solo con el trámite seleccionado, sin considerar directamente la pregunta.
        #        context = build_context_for_selected_tramite(df, selected_tramite)
        #        response = answer_questions([pregunta_final], context=context)[0]
        #        st.text_area("Respuesta:", value=response, height=150)

    #if 'tramite_seleccionado' in locals() or 'tramite_elegido' in locals():
    #    selected_tramite = tramite_seleccionado if 'tramite_seleccionado' in locals() else tramite_elegido
    #    preguntas_df = df[df['Trámite'] == selected_tramite]
    #    preguntas = preguntas_df['Pregunta_Completa'].dropna().unique()
    #    pregunta_seleccionada = st.selectbox("Selecciona una pregunta de tu interés o escribe una nueva abajo:", [''] + list(preguntas))

    #    if pregunta_seleccionada == '':
    #        nueva_pregunta = st.text_input("Ingresa tu nueva pregunta aquí:")
    #    else:
     #       nueva_pregunta = ''
        
        #nueva_pregunta = st.text_input("O ingresa tu nueva pregunta aquí:")
        
        #if st.button("Obtener Respuesta"):
        #    pregunta_final = nueva_pregunta if nueva_pregunta else pregunta_seleccionada
        #    if pregunta_final:
        #        context = build_context_for_selected_tramite(df, selected_tramite, pregunta=pregunta_final)
        #        response = answer_questions([pregunta_final], context=context)[0]
        #        st.text_area("Respuesta:", value=response, height=150)

if __name__ == "__main__":
    main()



#App
#def main():
#    st.set_page_config(page_title="Chat de Trámites Fiscales", page_icon="📎")
#    st.sidebar.header("Asistente de  IA para Trámites Fiscales")
#    st.title("IA Trámites Fiscales")
#    st.header(':blue[Asistente de  IA para Trámites Fiscales]', divider='blue')
#   st.subheader(':grey[Nuestro asistente automatizado responde tus preguntas sobre trámites fiscales]', divider='blue')

#if "openai_model" not in st.session_state:
#    st.session_state["openai_model"] = "gpt-3.5-turbo"

#if "messages" not in st.session_state:
#    st.session_state.messages = []
#st.write(df)

#for message in st.session_state.messages:
#    with st.chat_message(message["role"]):
#        st.markdown(message["content"])

#if prompt := st.chat_input("What is up?"):
#    st.session_state.messages.append({"role": "user", "content": prompt})
#    with st.chat_message("user"):
#        st.markdown(prompt)

#    with st.chat_message("assistant"):
#        stream = client.chat.completions.create(
#            model=st.session_state["openai_model"],
 #           messages=[
 #               {"role": m["role"], "content": m["content"]}
 #               for m in st.session_state.messages
#            ],
 #           stream=True,
 #       )
#        response = st.write_stream(stream)
 #   st.session_state.messages.append({"role": "assistant", "content": response})
