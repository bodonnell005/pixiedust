# -------------------------------------------------------------------------------
# Copyright IBM Corp. 2017
# 
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
# http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# -------------------------------------------------------------------------------
from pixiedust.display.app import *
import requests

@PixieApp
class MapboxBase():
    def setLayers(self, layers):
        self.layers = layers

    def getStyleTypeFromGeoJSON(self, layerDef, geoJSON):
        styleType = geoJSON['features'][0]['geometry']['type']
        if styleType == "Point":
            userStyleType = layerDef.get("type", "circle")
            if userStyleType == "symbol":
                return ("symbol", 
                    self.mergeDef( layerDef.get("paint"), {}), 
                    self.mergeDef( layerDef.get("layout"), {})
                )
            else:
                return ("circle", self.mergeDef( layerDef.get("paint"), {
                    "circle-color": "rgba(255,0,0,0.5)", 
                    "circle-radius": 5, 
                    "circle-blur": 0
                }), self.mergeDef( layerDef.get("layout"), {}))
        elif styleType == "MultiPolygon":
            return ("fill", self.mergeDef( layerDef.get("paint"), {
                "fill-color": "rgb(125, 125, 0)",
                "fill-opacity": 0.25,
                "fill-outline-color": "rgba(0,0,255, 0.5)"
            }), self.mergeDef( layerDef.get("layout"), {}))
        return ("line", self.mergeDef(layerDef.get("paint"), {
                "line-color": "rgba(128,0,128,0.65)",
                "line-width": 16,
                "line-blur": 2,
                "line-opacity": 0.75
            }), self.mergeDef( layerDef.get("layout"), {}))

    def mergeDef(self, userDef, defaultDef):
        if userDef is not None:
            defaultDef.update(userDef)
        return defaultDef
        
    def createMapboxGeoJSON(self, order, layerDef, geoJSON):
        id = layerDef["name"]
        style = self.getStyleTypeFromGeoJSON(layerDef, geoJSON)
        return {
            "id": id, 
            "maptype":"mapbox",
            "order": order,
            "source":{
                "type": "geojson",
                "data": geoJSON
            },
            "type": style[0],
            "paint": style[1],
            "layout": style[2]
        }

    def toggleLayer(self, index):
        fieldName = "layer{}".format(index);
        if hasattr(self, fieldName) and getattr(self, fieldName) is not None:
            setattr(self, fieldName, None)
        else:
            setattr(self, fieldName, self.createMapboxGeoJSON(index+2, self.layers[index], self.loadGeoJSON( self.layers[index]["url"] ) ))        
        
    def loadGeoJSON(self, url):
        def filterFeature(f):
            for key,value in iteritems(f):
                if value is None or "'" in value:
                    return True
            return False
        payload = requests.get(url).json()
        payload['features'] = [f for f in payload['features'] if not filterFeature(f['properties'])]
        return payload