
const SUBMIT_NEW_TEXT = 'Add Marker';
const SUBMIT_EDIT_TEXT = 'Update Marker';
const NEW_TYPE_DROPDOWN_OPTION = 'Create New Type';
let markerTypes = new Set();
let svg;

// Note: this is a primitive use of D3. Learn it better and
// make it look good. See:
// https://observablehq.com/@xianwu/force-directed-graph-network-graph-with-arrowheads-and-lab -->
let min_x=-1500, max_x=1400;
let min_y=-1350, max_y=800;
let height=800, width=800, margin=50;
let DEPTH_FILTER_MIN = 0
let DEPTH_FILTER_MAX = 2000

var allMarkers = []
var min_depth = DEPTH_FILTER_MIN
var max_depth = DEPTH_FILTER_MAX

var yAxisLength = height - 2 * margin,
    xAxisLength = width - 2 * margin;

var xScale = d3
      .scaleLinear()
      .domain([min_x, max_x])
      .range([0, xAxisLength]),
    yScale = d3
      .scaleLinear()
      .domain([max_y, min_y])
      .range([0, yAxisLength]);

function renderXAxis() {
    var xAxis = d3
      .axisBottom()
      // .ticks(lawfulness.length)
      // .tickFormat(t => {
      //   return lawfulness[t];
      // })
      .scale(xScale);

    svg
      .append("g")
      .attr("class", "x-axis")
      .attr("transform", function() {
        return "translate(" + margin + "," + (height - margin) + ")";
      })
      .attr("opacity", 1)
      .call(xAxis);

    d3.selectAll("g.x-axis g.tick")
      .append("line")
      .classed("grid-line", true)
      .attr("x1", 0)
      .attr("y1", 0)
      .attr("x2", 0)
      .attr("y2", -(height - 2 * margin))
      .attr("opacity", 0.4);

      return true;
  }

function renderYAxis() {
    var yAxis = d3
      .axisLeft()
        <!--
      // .ticks(goodness.length)
      // .tickFormat(t => {
      //   return goodness[t];
      // })
      -->
      .scale(yScale);

    svg
      .append("g")
      .attr("class", "y-axis")
      .attr("transform", function() {
        return "translate(" + margin + "," + margin + ")";
      })
      .call(yAxis);

    d3.selectAll("g.y-axis g.tick")
      .append("line")
      .classed("grid-line", true)
      .attr("x1", 0)
      .attr("y1", 0)
      .attr("x2", yAxisLength)
      .attr("y2", 0)
      .attr("fill", d3.rgb("#000000"));
  }

function isMarkerTypeEnabled(markerType) {
    return markerTypeCheckbox = document.querySelector("input.marker-type-checkbox[value='" + markerType + "']").checked;
}

function doesMarkerPassDepthFilter(marker) {
    return marker.depth <= max_depth && marker.depth >= min_depth
}

function onClickMarkerCircleElement(event) {
    var parentNode = event.target.parentNode
    var textNode = parentNode.querySelector('text')
    var titleNode = parentNode.querySelector('title')
    var circleNode = parentNode.querySelector('circle')

    // Find marker object
    var marker = allMarkers.filter(marker => marker.name == textNode.textContent)[0]

    // Populate edit form
    populateMarkerForm(marker)
}

function populateMarkerForm(marker) {
    document.querySelector('.new-bearing-form .new-bearing-name').value = marker.name
    document.querySelector('.new-bearing-form input[name="distance"]').value = marker.distance
    document.querySelector('.new-bearing-form input[name="depth"]').value = marker.depth
    document.querySelector('.new-bearing-form input[name="heading"]').value = marker.bearing
    document.querySelector('.new-bearing-form select[name="marker_type"]').value = marker.marker_type
    document.querySelector('.new-bearing-form input[name="marker_id"]').value = marker.id
    document.querySelector('.new-bearing-form input[name="submit"]').value = SUBMIT_EDIT_TEXT
}


function renderMarker(marker) {
    console.log("Rendering marker: " + marker.name)

    const node = svg //.selectAll(".nodes")
        //.data(dataset.nodes)
        // .enter()
        .append("g")
        .attr("class", "nodes")
        .attr("marker-type", marker.marker_type)
        .on("click", onClickMarkerCircleElement)

    let opacity = 1.0 - Math.min(-marker.depth / 1000.0, .8);

    node.append("circle")
        .attr("transform", function() {
            return "translate(" + margin + "," + margin + ")";
        })
//        .on("click", onClickMarkerCircleElement)
        .attr("cx", xScale(marker.x))
        .attr("cy", yScale(marker.y))
        .attr("fill", d3.rgb("#FF0000"))  // TODO: use marker-specific color instead
        .attr("opacity", opacity)
        .style("stroke", "black") //depth => depth > -1 ? "red" : undefined)
        .attr("r", 10);

    node.append("text")
        .attr("transform", function() {
            return "translate(" + margin + "," + margin + ")";
        })
        .attr("dy", yScale(marker.y) + 4)
        .attr("dx", xScale(marker.x) + 15)
        .text(marker.name);

    node.append("title")
        .text(marker.name);

//    return node

}

function titleCase(text) {
    return text.split('_').map(word => {
            return word.charAt(0).toUpperCase() + word.slice(1).toLowerCase();
        }).join(' ');
}

function renderLegend() {
    Array.from(markerTypes).sort().forEach(marker_type => {
        addLegendItem(marker_type)
    })

    document.querySelector(".legend-clear-all").addEventListener("click", function() {legendSetAll(false)})
    document.querySelector(".legend-check-all").addEventListener("click", function() {legendSetAll(true)})
    document.querySelector(".marker-type-dropdown").addEventListener("change", function() {handleDropdownSelection()})
    return true
}

function addLegendItem(marker_type, marker_color) {
    let legendDiv = document.querySelector('.legend')
    let markerTypeDiv = document.createElement('div')
    legendDiv.appendChild(markerTypeDiv)

    addLegendItemCheckbox(marker_type, markerTypeDiv)
    addLegendItemLabel(marker_type, markerTypeDiv)
}

function addLegendItemCheckbox(marker_type, markerTypeDiv) {
    var checkbox = document.createElement('input')
    checkbox.setAttribute("type", "checkbox")
    checkbox.setAttribute("value", marker_type)
    checkbox.checked = true;
    checkbox.classList.add("marker-type-checkbox")
    markerTypeDiv.appendChild(checkbox)
    checkbox.addEventListener('click', checkboxClickListener)
}

function handleDropdownSelection() {
    const markerTypeDropdown = document.querySelector('.marker-type-dropdown')
    const markerTypeInput = document.querySelector('.marker-type-input')
    markerTypeInput.value = markerTypeDropdown.value
}

function addLegendItemLabel(marker_type, markerTypeDiv) {
    var label = document.createElement('label')
    label.setAttribute("for", marker_type)
    label.textContent  = marker_type
    markerTypeDiv.appendChild(label)
}
function checkboxClickListener(e) {
    var checkbox = e.target
    d3.selectAll(".nodes[marker-type='" + checkbox.value + "']")
        .style("opacity", (checkbox.checked ? 1 : 0))
}

function legendSetAll(checked) {
    document.querySelectorAll("input[type=checkbox]").forEach(checkbox => {
        if (checkbox.checked !== checked) {
            checkbox.click()
        }
    })
    renderMarkers()
}

function buildMarkerTypesSet(markers) {
    markers.forEach(marker => {
        markerTypes.add(marker.marker_type)
    })
    return true
}

function renderMarkers() {

    allMarkers.forEach(marker => {
        if (doesMarkerPassDepthFilter(marker) &&
            isMarkerTypeEnabled(marker.marker_type)) {
            renderMarker(marker)
        }
    })

//    svg.selectAll('.nodes')
//        .data(markers)
//        .enter()
//            .append("g")
//            .attr("class", "nodes")
//        .enter().append(function(marker) { return renderMarker(marker) })
////            .each(renderMarker)

}

function clearAllMarkers() {
    document.querySelectorAll('.nodes').forEach(node => {
        document.querySelector('.axis').removeChild(node)
        });
}

function populateMarkerTypeDropdowns() {
    document.querySelectorAll('.marker-type-dropdown').forEach(dropdown => {
        while (dropdown.options.length > 0) {
            dropdown.remove(dropdown.options.length-1)
        }
        Array.from(markerTypes).forEach(marker_type => {
            var option = document.createElement('option')
            option.setAttribute('value', marker_type)
            option.textContent = marker_type
            dropdown.appendChild(option)
        })
    })
}

function renderMap(mapData) {
    svg = d3
        .select(".plot")
        .append("svg")
        .attr("class", "axis")
        .attr("width", width)
        .attr("height", height);

    allMarkers = mapData

    Promise.all([renderXAxis(), renderYAxis(), buildMarkerTypesSet(allMarkers)])
    Promise.resolve(renderLegend())
    Promise.resolve(renderMarkers())
    populateMarkerTypeDropdowns()
}

function onDepthFilterChanged(range) {
    [min_depth, max_depth] = range

    // TODO: might need to use a Transition here:
    // see https://www.oreilly.com/library/view/d3-for-the/9781492046783/ch04.html

    clearAllMarkers()
    renderMarkers()

    d3.select('p#value-range').text(range.map(d3.format(',d')).join('-'));
}


function initializeDepthSlider() {

    // Range slider
/*
    <p id="value-range"></p>
    <div id="slider-range"></div>
*/
    var sliderRange = d3
        .sliderBottom()
        .min(0)
        .max(2000)  // d3.max(data))
        .width(300)
        .tickFormat(d3.format(',d'))
        .ticks(5)
        .default([0, 2000])
        .fill('#2196f3')
        .on('onchange', val => { onDepthFilterChanged(val) });

    var gRange = d3
        .select('div#slider-range')
        .append('svg')
        .attr('width', 500)
        .attr('height', 100)
        .append('g')
        .attr('transform', 'translate(30,30)');

    gRange.call(sliderRange);

    d3.select('p#value-range').text(
        sliderRange
            .value()
            .map(d3.format(',d'))
            .join('-')
        );

}
