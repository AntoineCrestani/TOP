import dash_html_components as html
import dash_leaflet as dl
from itinerary_functs import *
from dash import Dash



# here i recreate everything because it was easier to code it this way for my brain. the next section could be replaced by a call to an api that returns "Global_itineraire"
# creating user profile
profil=[1 for k in ADJUSTED_TYPES]
datatourisme_df=pd.read_csv("poi.csv")
u_region = "Occitanie"
u_start_poi_uuid="43/b9824e30-cdd5-39d8-a5d1-ec681a91e378"
u_start_point=get_pos(u_start_poi_uuid,datatourisme_df)
u_nb_jour = 6
u_moyen_mobilite = "Voiture" # Marche/ Velo / Voiture
u_categorie = None
u_nb_pts_max = 48 # temps min de visite 30 minutes = 24H par jour
num_clusters=NUM_CLUSTER_BY_TRANSPORT[u_moyen_mobilite]

clustered, path_through_clusters,global_itineraire,kmeans,predictions,G= main_func(profil,u_start_poi_uuid,num_clusters,u_moyen_mobilite,u_nb_jour,seed=133)



# here is what's important : 

stops = []

for day in range(len(global_itineraire.keys())):
        trajet= global_itineraire[list(global_itineraire.keys())[day]]
        color_idx=day
        #color = color_palette[color_idx]
        #icon_color = 'dimgray' if color == 'white' else 'white'
        for idx_poi in range(len(trajet)):
            poi=trajet[idx_poi]
            nom="Jour1, etape 1 : \n" + datatourisme_df[datatourisme_df["URI_ID_du_POI"]==poi]["Nom_du_POI"]
            location= get_pos(poi,datatourisme_df)
            stops.append(dict(title=nom,position=[location[0],location[1]]))
            #
app = Dash()
app.layout = html.Div([
    dl.Map(children=[dl.TileLayer()] + [dl.Marker(**stop) for stop in stops],
           style={'width': '100%', 'height': '50vh', 'margin': "auto", "display": "block"}, id="map"),
])








if __name__ == '__main__':
    app.run_server()