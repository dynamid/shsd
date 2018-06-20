function myFunction(){
  console.log("bouyaaa");
}
//------- afficher map + markers
function printMap(center,geojson){ // {{center_map}},'{{geojson}}'
  console.log(center);
  L.mapbox.accessToken = 'pk.eyJ1IjoiY3lsaWEiLCJhIjoiY2poNmZwcW1mMDJ4ZTJ3cGc5dmo1NzA1NyJ9.JU-g1DpPB6jTT-tiVYcUgw';
  var coord = center;
  console.log(coord);
  var map = L.mapbox.map(document.getElementById('map'))
    .addLayer(L.mapbox.tileLayer('mapbox.streets'));
  var myLayer = L.mapbox.featureLayer().addTo(map);
  myLayer.loadURL(geojson); //charge le contenu du // '/api/geoJson/user'
  map.fitBounds([[coord[0],coord[1]], [coord[2],coord[3]]]);

  return map;

}

//------- afficher popupp
function printPopup(){
  map.on('click', 'places', function(e) {
    var coordinates = e.features[0].geometry.coordinates.slice();
    var description = e.features[0].properties.description;
    while (Math.abs(e.lngLat.lng - coordinates[0]) > 180) {
      coordinates[0] += e.lngLat.lng > coordinates[0] ? 360 : -360;
    }
    new mapboxgl.Popup()
      .setLngLat(coordinates)
      .setHTML(description)
      .addTo(map);
  });
  return map;
}


//------- Changer le curseur quand il est sur un marker
function changeCursor(){
  map.on('mouseenter', 'places', function() {
    map.getCanvas().style.cursor = 'pointer';
  });
  return map;
}

//------- Rechanger le curseur quand il sort du marker
function rechangeCursor(){
  map.on('mouseleave', 'places', function() {
    map.getCanvas().style.cursor = '';
  });
}


//------- Créer la légende à ajouter
function addLegend(my_colors,map){//{{colors_to_print | tojson}}
  console.log("dans addLegend : " + my_colors);
  var legend = document.createElement("div");
  var colors = my_colors;
  var colors_json = JSON.parse(colors);

  //-----------ADD LEGEND
  var div = document.createElement('div');
  var col = L.control({
    position: 'bottomright'
  });
  console.log("col : " +col.getContainer());
  col.onAdd = function(map) {
    console.log("youhou");
    var legend = document.createElement('div')
    legend.id = "legend";
    legend.height = 100;
    for (i = 0; i < colors_json.legend.length; i++) {
      var elt = document.createElement('div');
      var value = document.createElement('span');
      value.innerHTML = colors_json.legend[i].asn;

      var key = document.createElement('span');
      key.className = 'legend-key';
      key.style.backgroundColor = colors_json.legend[i].color;

      elt.appendChild(key);
      elt.appendChild(value);
      legend.appendChild(elt);
    }
    var div = L.DomUtil.create('div', 'myclass');
    div.innerHTML = legend.outerHTML;
    return div;
  }
  console.log("col2 : "+ col.getContainer());
  col.addTo(map);
  map.legendControl.addLegend(document.getElementById('legend').innerHTML);
}
