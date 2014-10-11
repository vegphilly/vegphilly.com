var _ = require('lodash'),
    $ = require('jquery'),
    google = require('google');


/////////////////////////////////////
// TEMPLATES
/////////////////////////////////////

var summaryCaptionTemplate = [
    '<strong><a id="captionBubble_hyperlink" class="uline" href="<%= url %>"><%= name %></a></strong><br/>',
    '<%= address %><br/>',
    '<%= phone %><br/>'].join(""),
    detailCaptionTemplate = '<strong><%= name %></strong><br/>',

    // TODO: all of this can be abstracted beyond veg level to allow coloring by anything
    vegLevelCategoryMapping = {
        1: 'vegan',
        2: 'vegetarian',
        3: 'vegetarian',
        4: 'vegetarian',
        5: 'omni',
        6: 'omni',
        7: 'omni',
        0: 'omni' // There is no zero in postgres, but we are coercing nulls to 0
    },
    vegCategoryMarkerMapping = {
        'vegan': '/static/images/marker-vegan.png',
        'vegetarian': '/static/images/marker-vegetarian.png',
        'omni': '/static/images/marker-omni.png'
    };

/////////////////////////////////////
// MAP WRAPPER OBJECT
/////////////////////////////////////

var vendorMap = {
    initialize: function(map_container_id, vendors, mapType, autoResize, defaultCenter) {
        this.vendors = vendors;
        this.captionBubble = new google.maps.InfoWindow();
        this.map = null;
        this.markers = {};
        this.markerImage = null;

        var center = defaultCenter || this.getBounds().getCenter();

        this.map = new google.maps.Map($(map_container_id).get(0),
                                       {
                                           zoom: 14,
                                           maxZoom: 18,
                                           minZoom: 9,
                                           center: center,
                                           mapTypeId: google.maps.MapTypeId.ROADMAP
                                       });


        this.mapType = mapType;
        if (mapType === "summary") {
            this.captionTemplate = summaryCaptionTemplate;
            // this.markerImage = "//www.google.com/mapfiles/marker.png";
        } else if (mapType === "detail") {
            this.captionTemplate = detailCaptionTemplate;
            // this.markerImage = "//www.google.com/mapfiles/arrow.png";
        }

        if (autoResize === true) {
            vendorMap.redrawToBounds();
        }

        vendorMap.plotAllPoints();
    },

    plotAllPoints: function() {
        _.each(this.vendors, function(vendor) {
            this.markers[vendor.id] = this.place(vendor);
        }, this);
    },

    getBounds: function () {
        var bounds = new google.maps.LatLngBounds();
        if (this.vendors.length === 0) {
            bounds.extend(this.map.getCenter());
        }
        _.each(this.vendors, function(vendor) {
            var LatLng = new google.maps.LatLng(vendor.latitude, vendor.longitude);
            bounds.extend(LatLng);
        });
        return bounds;
    },

    redrawToBounds: function () {
        this.map.fitBounds(this.getBounds());
    },


    place: function(vendor) {
        var image = null,
            latLng = new google.maps.LatLng(vendor.latitude, vendor.longitude),
            marker = null,
            vendorMap = this,
            bodyText = _.template(this.captionTemplate)(vendor);

        if (this.mapType === 'summary') {
            // convert veg level to super category and then lookup an icon for that category
            // TODO make this more readable.
            image = new google.maps.MarkerImage(vegCategoryMarkerMapping[vegLevelCategoryMapping[vendor.vegLevel]]);
        } else if (this.mapType === 'detail') {
            image = new google.maps.MarkerImage("/static/images/vegphilly-carrot-map-logo.png");
        }

        marker = new google.maps.Marker({
                position: latLng,
                icon:image,
        });
        marker.setMap(this.map);

        if (bodyText) {
            google.maps.event.addListener(marker, 'click', function () {
                vendorMap.captionBubble.setContent(bodyText);
                vendorMap.captionBubble.open(vendorMap.map, this);
    	    });
        }
        return marker;
    }
};

module.exports = {
    vendorMap: vendorMap,
    vegLevelCategoryMapping: vegLevelCategoryMapping,
    vegCategoryMarkerMapping: vegCategoryMarkerMapping
};

