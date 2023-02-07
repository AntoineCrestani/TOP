import dash 
import dash_mantine_components as dmc
import dash_bootstrap_components as dbc
from dash import html,dcc 
from dash.dependencies import Input,Output
from dash import Dash, html
from itinerary_functs import *
from userProfile import *
import folium
app = dash.Dash(__name__)

app = dash.Dash(
    external_stylesheets=[dbc.themes.BOOTSTRAP]
)
   
app.layout = html.Div([
   ])   



from dash import dcc,dash,html
from dash.dependencies import Input, Output, State

app = dash.Dash()





app.layout = html.Div([
    html.H3("Quelle catégorie d'age vous correspond le mieux ?"),
    dcc.Dropdown(
        id="age",
        options=[{"label":"18-25", "value":"18-25"},
                {"label":"25-35", "value":"25-35"},
                {"label":"35-45", "value":"35-45"},
                {"label":"45-55", "value":"45-55"},
                {"label":"55-70", "value":"55-70"},
                {"label":"70+", "value":"70+"}],
        ), 
    html.H3("Voyagez vous avec des enfants en bas age (moins de 5 ans)?"),
    dcc.Dropdown(
        id="babies",
        options=[{"label":"Oui", "value":"YES"},
                {"label":"Non", "value":"NO"}],
        ), 
    html.H3("Quel est votre budget?"),
    dcc.Dropdown(
        id="budget",
        options=[{"label":"Petit", "value":"cheap"},
                {"label":"Moyen", "value":"medium"},
                {"label":"Gros", "value":"expensive"}],
        ),
    html.Br(),
    html.Button(id='Submit_form', n_clicks=0, children='Submit'),
    html.Div(id='map'),
])


@app.callback(
    [Output('map', 'children')],
    [Input('Submit_form', 'n_clicks')],
    [State('age', 'value'),
     State('babies', 'value'),
     State('budget', 'value')])
def update_map(n_clicks, age, babies, budget):
    print( "n_clicks is ",str(n_clicks))
    print(age,babies,budget)
    datatourisme_df=pd.read_csv("poi.csv")
    profil=genere_profil_utilisateur(age,babies,budget,categories=[],file=FILE)
    u_start_point=(43.76587273970739, 1.5109121106288823)
    u_nb_jour = 10
    u_moyen_mobilite = "Marche" # Marche/ Velo / Voiture
    start_poi_uuid=get_nearest_point(datatourisme_df,u_start_point)
    start_point=get_pos(start_poi_uuid,datatourisme_df)
    nb_pts_max = 48 # temps min de visite 30 minutes = 24H par jour
    num_clusters=NUM_CLUSTER_BY_TRANSPORT[u_moyen_mobilite]
    # on génere l'itinéraire
    clustered, path_through_clusters,global_itineraire,kmeans,predictions,G= main_func(profil,start_poi_uuid,num_clusters,u_moyen_mobilite,u_nb_jour,seed=133)
    #on crée notre carte
    itineraire_map = folium.Map(location = u_start_point , tiles = "OpenStreetMap", zoom_start = ZOOM_LVL[u_moyen_mobilite])
    itineraire_map = plot_itineraire(global_itineraire,clustered,itineraire_map,color_palette=FOLIUM_COLORS,icon='star')
    #on la sauvegarde
    itineraire_map.save("plot_itineraire.html")
    return [html.Div([html.H1('Your list of stops'),html.Iframe(id='map', srcDoc=open('plot_itineraire.html', 'r').read(), width='600px', height='600px')])]


if __name__ == '__main__':
    app.run_server(debug=False)

