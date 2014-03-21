var ConnectorFiles = {};

ConnectorFiles.connectorId = _.last(window.location.pathname.split("/"));

ConnectorFiles.File = Backbone.Model.extend({
    defaults: {
        name: '',
        id: '',
    }
});

ConnectorFiles.Collection = Backbone.Collection.extend({
    url: ['/v1/connectors', ConnectorFiles.connectorId].join("/"),
    model: ConnectorFiles.File
});

ConnectorFiles.Views = {};

ConnectorFiles.Views.Edit = Backbone.View.extend({
    change: function () {
        this.model.set({
            name: $(this.el).children('input').val()
        });
        this.model.save();
    },
    destroy: function () {
        var el = this.el;
        this.model.destroy({
            success: function () {
                $(el).remove();
            }
        });
    },
    events: {
        'click .btn-download': 'open',
        'click .btn-remove': 'destroy',
        'change input': 'change'
    },

    open: function() {
        window.open(['/v1/connectors', ConnectorFiles.connectorId, 'files', this.model.get("id"), "download"].join("/"));
    },

    initialize: function () {
        _(this).bindAll('change', 'destroy', 'render');
    },
    render: function () {
        $('#connectorfile-template').tmpl(this.model.toJSON()).appendTo(this.el);
        this.delegateEvents();
    }
});

ConnectorFiles.Views.List = Backbone.View.extend({
    append: function (model) {
        var p = $('<div class="row">').appendTo('#connectorfiles'),
            view = new ConnectorFiles.Views.Edit({
                model: model,
                el: p[0]
            });
        view.render();
    },
    initialize: function () {
        _(this).bindAll('append', 'render');
        this.collection.bind('refresh', this.render);
        this.collection.bind('add', this.append);
    },
    render: function () {
        $('#connectors').empty();
        this.collection.each(function (model) {
            this.append(model);
        }, this);
    }
});

$(function () {
    var collection = new ConnectorFiles.Collection(),
        view = new ConnectorFiles.Views.List({
            collection: collection
        });

    collection.fetch();

});
