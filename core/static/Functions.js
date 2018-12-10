function iconElement() {
    var x = document.getElementById("header");
    if (x.className === "topnav") {
        x.className += " responsive";
    } else {
        x.className = "topnav";
    }
}
//------- afficher map + markers
function printMap(center, geojson) { // {{center_map}},'{{geojson}}'
  L.mapbox.accessToken = 'pk.eyJ1IjoiY3lsaWEiLCJhIjoiY2poNmZwcW1mMDJ4ZTJ3cGc5dmo1NzA1NyJ9.JU-g1DpPB6jTT-tiVYcUgw';
  var coord = center;
  var map = L.mapbox.map(document.getElementById('map'))
    .addLayer(L.mapbox.tileLayer('mapbox.streets'));
  var myLayer = L.mapbox.featureLayer().addTo(map);
  myLayer.loadURL(geojson); //charge le contenu du // '/api/geoJson/user'
  map.fitBounds([
    [coord[0], coord[1]],
    [coord[2], coord[3]]
  ]);

  return map;

}

//------- afficher popupp
function printPopup() {
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
function changeCursor() {
  map.on('mouseenter', 'places', function() {
    map.getCanvas().style.cursor = 'pointer';
  });
  return map;
}

//------- Rechanger le curseur quand il sort du marker
function rechangeCursor() {
  map.on('mouseleave', 'places', function() {
    map.getCanvas().style.cursor = '';
  });
}

//------- Créer la légende à ajouter
function addLegend(my_colors, map) { //{{colors_to_print | tojson}}
  var legend = document.createElement("div");
  var colors = my_colors;
  var colors_json = JSON.parse(colors);
  // if no logs
    if (colors_json.legend.length === 0){
      var to_add = {asn: "No connection to print", color: "#ffffff"};
      colors_json.legend.push(to_add);
    }
    console.log(colors_json);
  //-----------ADD LEGEND
  var div = document.createElement('div');
  var col = L.control({
    position: 'bottomright'
  })
  col.onAdd = function(map) {
    var legend = document.createElement('div')
    legend.id = "legend";


    var btn_conteneur = document.createElement('div');
    btn_conteneur.id = "btn_conteneur"
    var btn = document.createElement('button');
    var btn_text = document.createTextNode("-");
    btn.id = "btn";
    btn.class="w3-button w3-xlarge w3-circle w3-teal";
    btn.appendChild(btn_text);
    btn_conteneur.appendChild(btn);


    for (i = 0; i < colors_json.legend.length; i++) {
      var elt = document.createElement('div');
      elt.id = "elt";

      var asn_text = document.createElement('span');
      asn_text.id = "value";
      asn_text.innerHTML = colors_json.legend[i].asn;

      var asn_color = document.createElement('span');
      asn_color.className = 'legend-key';
      asn_color.style.backgroundColor = colors_json.legend[i].color;

      elt.appendChild(asn_color);
      elt.appendChild(asn_text);
      legend.appendChild(elt);
    }
    var conteneur = L.DomUtil.create('div', 'myclass');
    conteneur.id = "conteneur"
    conteneur.innerHTML =legend.outerHTML + btn_conteneur.outerHTML;
    return conteneur;
  }
  col.addTo(map);
  //map.legendControl.addLegend(document.getElementById('legend').innerHTML);

  handleClick();
}
//------------croix sur legende
function handleClick() {

  let btn = document.getElementById('btn');
  let div = document.getElementById('conteneur');
  btn.addEventListener('click', function(event){
    if (div.classList.contains('is-hidden')) {
      div.classList.remove('is-hidden');
      btn.innerHTML = "-";
    } else {
      div.classList.add('is-hidden');
      btn.innerHTML = "+";
    }
  });
}
