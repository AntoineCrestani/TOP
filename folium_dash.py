
from dash import Dash, html
from itinerary_functs import *

import folium

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
stops=[]
for day in range(len(global_itineraire.keys())):
        trajet= global_itineraire[list(global_itineraire.keys())[day]]
        color_idx=day
        #color = color_palette[color_idx]
        #icon_color = 'dimgray' if color == 'white' else 'white'
        #Le numéro de jour
        for idx_poi in range(len(trajet)):
            
            
            poi=trajet[idx_poi]
            nom="Jour "+ str(day -1)+", étape"+str(idx_poi)+"\n" + datatourisme_df[datatourisme_df["URI_ID_du_POI"]==poi]["Nom_du_POI"]
            location= get_pos(poi,datatourisme_df)
            stops.append(dict(title=nom,position=[location[0],location[1]]))



itineraire_map = folium.Map(location = u_start_point , tiles = "OpenStreetMap", zoom_start = ZOOM_LVL[u_moyen_mobilite])
plot_itineraire(global_itineraire,clustered,itineraire_map,color_palette=FOLIUM_COLORS,icon='star')
itineraire_map.save("plot_itineraire.html")
app = Dash()

app.layout = html.Iframe(id="map",srcDoc=open("plot_itineraire.html","r"),
                    style={"height": "1067px", "width": "100%"})



if __name__ == '__main__':
    app.run_server()
