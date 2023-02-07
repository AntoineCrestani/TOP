
from dash import Dash, html
from itinerary_functs import *

import folium

#here i recreate everything because it was easier to code it this way for my brain. the next section could be replaced by a call to an api that returns "Global_itineraire"
#creating user profile
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
# on génere l'itinéraire
clustered, path_through_clusters,global_itineraire,kmeans,predictions,G= main_func(profil,u_start_poi_uuid,num_clusters,u_moyen_mobilite,u_nb_jour,seed=133)








#on crée notre carte
itineraire_map = folium.Map(location = u_start_point , tiles = "OpenStreetMap", zoom_start = ZOOM_LVL[u_moyen_mobilite])
plot_itineraire(global_itineraire,clustered,itineraire_map,color_palette=FOLIUM_COLORS,icon='star')
#on la sauvegarde
itineraire_map.save("plot_itineraire.html")


#TODO : faire des fonctions qui encapsule  lignes du dessus+ sauvegarde
#       Obtenir les input avec le code de Amey
#       finir la génération de profils
#       Implémenter la génération de profil dans le site.

#       Faire tout ca avec l'api et la bdd....

app = Dash()



app.layout = html.Div([
    html.H1('My first app with folium map'),
    html.Iframe(id='map', srcDoc=open('plot_itineraire.html', 'r').read(), width='50%', height='600'),
    html.Button(id='map-submit-button', n_clicks=0, children='Submit')
])





if __name__ == '__main__':
    app.run_server(debug=True)
