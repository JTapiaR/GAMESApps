import streamlit as st
st.set_page_config(
    page_title="Inicio",
    page_icon="👋",
)

logo_url = "GAMESlogo.png"  # Reemplaza con la ruta de tu logo
st.image(logo_url, width=400)

st.write("# Bienvenido a GAMES Economics APPS! 👋")
st.divider()

st.sidebar.success("Selecciona un demo.")

st.markdown(
    """
    Nuestras apps te permiten  consultar diversos documentos útiles 
    pra el trabajo cotidiano de profesionistas en Derecho, Contabilidad,  y
    Administración. 


    **👈 Selecciona la aplicación de tu interés en el menú de la izquierda**

    - ### 🤖	:page_facing_up: Chatbot Fiscal "Anexo 1-A de la Resolución Miscelánea Fiscal 2024"
      -Selecciona la modalidad de búsqueda de tu trámite o servicio
      Puedes realizar la búsqueda por el fundamento legal o describiendo
      el trámite/servicio de tu interés.

      -Selecciona la pregunta de tu  interés o ingresa una 
      pregunta personalizada
      
      -Obten tu respuesta

    - ### 📊 Analítica de Texto
      -Elige la fecha del DOF que quieres consultar

      -Selecciona la Dependencia o institución de tu interés

      -Selecciona las publicaciones que te interesn y  listo!

      -Visualiza analítica de texto de estas publicaciones

    - ### 🔊 Resumenes de Texto y Texto a audio
     -Obten con IA el resumen de las publicaciones seleccionadas

     -Transforma con IA el texto del resumen en audio


     
    - ### ¿Tienes dudas o comentarios?
    
    - ### ¿Quieres implementar estas aplicaciones en tu negocio?

     Contáctanos en boliva@gamesecon.com
 """
)