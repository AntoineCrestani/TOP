from dash import Dash, html
from itinerary_functs import *
from userProfile import *
import folium
datatourisme_df=pd.read_csv("poi.csv")
#here i recreate everything because it was easier to code it this way for my brain. the next section could be replaced by a call to an api that returns "Global_itineraire"
#creating user profile

# lets say the user has the following characteristics :

age_group="18-25"
children="NO"
categories=[("Artistic",5),("NaturalHeritage",3),("LocalCulture",2)]
affordable = "cheap"
profil=genere_profil_utilisateur(age_group,children,affordable,categories,file=FILE)

# lets define the itinerary characteristics :
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


#TODO : faire des fonctions qui encapsule  lignes du dessus+ sauvegarde
#       Obtenir les input avec le code de Amey
#       finir la génération de profils
#       Implémenter la génération de profil dans le site.

#       Faire tout ca avec l'api et la bdd....

app = Dash()



app.layout = html.Div([
    html.H1('Your list of stops'),
    html.Iframe(id='map', srcDoc=open('plot_itineraire.html', 'r').read(), width='300px', height='300px'),
    html.Button(id='map-submit-button', n_clicks=0, children='Submit')
])





if __name__ == '__main__':
    app.run_server(debug=True)
