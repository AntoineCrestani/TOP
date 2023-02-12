from city_names import cities
from dash import Dash, dcc, dash, html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
from userProfile import *
import folium
import os
import calendar
import time
from itinerary_DB import Itinerary_DB as IT_DB

FOLIUM_COLORS = [
    'red', 'blue', 'green', 'purple', 'orange', 'darkred',
    'lightred', 'beige', 'darkblue', 'darkgreen', 'cadetblue',
    'darkpurple', 'white', 'pink', 'lightblue', 'lightgreen', 'gray', 'black', 'lightgray'
]

# Zoom a appliquer sur la carte
ZOOM_LVL = {
    'car': 8,
    'bike': 8,
    'walk': 8
}

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(
    external_stylesheets=[dbc.themes.BOOTSTRAP])


city_datalist = html.Datalist(
    id='list-suggested-cities',
    children=[html.Option(value=city.strip("/\s /\n /\t /\"   "))
              for city in cities]
)


app.layout = html.Div(
    children=[
    html.Header(className="top", children=html.H1(
        "TOP : The Occitania Project")),
    dbc.Row(className="test",
            children=[
                dbc.Col(className="col left",
                children=[
                        dbc.Row(
                            children=[
                                html.H3("Visitez l'occitanie", 
                                    className="heading_1"),
                                html.H3("Planifiez votre itinéraire en quinze secondes",
                                    className="heading_2"),
                                html.H3("Catégorie d'age *",
                                        className="text_query"),
                                dcc.Dropdown(className="dropdown",
                                             id="age",
                                             options=[{"label": "18-25", "value": "18-25"},
                                                      {"label": "25-35",
                                                      "value": "25-35"},
                                                      {"label": "35-45",
                                                      "value": "35-45"},
                                                      {"label": "45-55",
                                                      "value": "45-55"},
                                                      {"label": "55-70",
                                                          "value": "55-70"},
                                                      {"label": "70+", "value": "70+"}]
                                             ),
                                html.H3("Enfants en bas age (moins de 5 ans) *",
                                        className="text_query"),
                                dcc.Dropdown(className="dropdown",
                                             id="babies",
                                             options=[{"label": "Oui", "value": "YES"},
                                                      {"label": "Non", "value": "NO"}]
                                             ),
                                html.H3("Budget ", className="text_query"),
                                dcc.Dropdown(className="dropdown",
                                             id="budget",
                                             options=[{"label": "Petit", "value": "cheap"},
                                                      {"label": "Moyen",
                                                      "value": "medium"},
                                                      {"label": "Gros", "value": "expensive"}]
                                             ),
                                html.H3("Moyen de transport? *",
                                        className="text_query"),
                                dcc.Dropdown(className="dropdown",
                                             id="transport",
                                             options=[{"label": "With Private cars.", "value": "car"},
                                                      {"label": "Riding on bikes!",
                                                      "value": "bike"},
                                                      {"label": "walking...", "value": "walk"}]
                                             ),
                                html.H3("Ville de départ *",
                                        className="text_query"),
                                dcc.Dropdown(className="dropdown",
                                             id="city_dd",
                                             options=[{"label": city.strip("/\n /\t /\"   "), "value": city.strip("/\n /\t /\"   ")} for city in cities]
                                             ),
                                html.H3("Durée de voyage *",
                                        className="text_query"),
                                dcc.Dropdown(className="dropdown",
                                             id="duree",
                                             options=[{"label": f"{k} jours", "value": k}
                                                      for k in range(1, 11)]
                                             ),
                                html.Br(),
                                html.Button(id='Submit_form', n_clicks=0,
                                            children='Submit', className="bouton")
                            ]
                        )
                    ]
                        ),
                dbc.Col(className="col right",
                children=[
                            dbc.Row(
                                [
                                    html.Div(id="map",className="container_map",children=[
                                        html.H1("Loading")
                                    ])])]
                    
                )
            ]),
]
)


@app.callback(
    Output('map', 'children'),
    [Input('Submit_form', 'n_clicks')],
    [State('age', 'value'),
     State('babies', 'value'),
     State('budget', 'value'),
     State('transport', 'value'),
     State('city_dd', 'value'),
     State('duree', 'value')])
def update_map(n_clicks, age, babies, budget, transport, city_dd, duree):
    #on click, we create an itinerary and then a map to display it
    print("categorie age is", age,"babies is ", babies,"budget is", budget)
    print(city_dd)
    if age and babies and budget and transport and city_dd and duree:
        # datatourisme_df=pd.read_csv("poi.csv")
        # getting profile
        profil = genere_profil_utilisateur(age, babies, budget, categories=[
        ], file=os.path.join(os.getcwd(), "dump/data_antoine.tsv"))

        # user dummy values

        u_nb_jour = int(duree)
        u_moyen_mobilite = transport  # walk, bike, car
        it_db = IT_DB({ "u_nb_days": u_nb_jour,
                      "u_tr_type": transport, "u_city": city_dd, "profile": profil})
        
        print(it_db.it_ml.clustered["Cluster"])
        # on génere l'itinéraire
        # clustered, path_through_clusters,global_itineraire,kmeans,predictions,G= main_func(profil,start_poi_uuid,num_clusters,u_moyen_mobilite,u_nb_jour,seed=133)
        # on crée notre carte
        # it_db.nearest_POI_ID
        itineraire_map = folium.Map(location=it_db.it_ml.start_pos, tiles="OpenStreetMap",
                                    zoom_start=ZOOM_LVL[u_moyen_mobilite], min_zoom=8)
        itineraire_map = plot_itineraire(
            it_db.it_ml.global_itineraire, it_db.it_ml.clustered, itineraire_map, color_palette=FOLIUM_COLORS, icon='star')
        # on la sauvegarde
        ts = calendar.timegm(time.gmtime())
        itineraire_map.save(os.path.join(
            os.getcwd(), "htmls\\carte_"+str(ts)+".html"))
        # create a json to save the user profile, with a timestamp,
        # associate the aforementioned timestamp in the html file too, 4future
        return [html.Div(className="container_map",
                         children=[html.H1('Your list of stops'),
                                   html.Iframe(id='map', className="carte_display",srcDoc=open(os.path.join(os.getcwd(), f"htmls\\carte_{ts}.html"), "r",encoding="utf-8").read())])]
    else:
        return [html.Div(className="container_map",
        children=[
                html.Iframe( className="carte_display",srcDoc=open(os.path.join(os.getcwd(
                ), f"src\\assets\\base_map.html"), "r",encoding="utf-8").read())
                ])]


def plot_itineraire(itineraire, df, map_to_plot, color_palette=FOLIUM_COLORS, icon='star'):
    # setup first POI, otherwise it doesnt work too well.
    first_poi = itineraire[list(itineraire.keys())[0]][0]
    nom = df[df["id"] == first_poi]["name"]
    color = color_palette[0]
    icon_color = 'dimgray' if color == 'white' else 'white'
    folium.Marker(location=get_pos(first_poi, df),
                  popup=f"<h5>Jour 1, etape 1 </h5><p>{nom.item()}</p>",
                  icon=folium.Icon(
                      color=color_palette[0], icon_color=icon_color, icon=icon)
                  ).add_to(map_to_plot)
    for day in range(len(itineraire.keys())):
        # on parcourt les jours
        print(f"day {day}")
        trajet = itineraire[list(itineraire.keys())[day]]
        color_idx = day
        color = color_palette[color_idx]
        icon_color = 'dimgray' if color == 'white' else 'white'
        for idx_poi in range(1, len(trajet)):

            poi = trajet[idx_poi]
            nom = df[df["id"] == poi]["name"]

            print(get_pos(poi, df))
            folium.Marker(
                location=get_pos(poi, df),
                popup=f"<h5>Jour {day+1} , etape {idx_poi+1}</h5><p>{nom.item()}</p>",
                icon=folium.Icon(color=color, icon_color=icon_color, icon=icon)
            ).add_to(map_to_plot)
    return map_to_plot


def get_pos(POI_URI, df):
    return (df[df["id"] == POI_URI]["lat"].item(), df[df["id"] == POI_URI]["long"].item())


if __name__ == '__main__':
    app.run_server(debug=False)
