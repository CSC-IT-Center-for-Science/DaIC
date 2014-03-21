var Connectors = {};

Connectors.Container = Backbone.Model.extend({
    defaults: {
        id: '',
        updated: ''
    }
});

Connectors.Collection = Backbone.Collection.extend({
    model: Connectors.Container,
    url: '/v1/connectors'
});

Connectors.Views = {};

Connectors.Views.Edit = Backbone.View.extend({
    destroy: function () {
        var el = this.el;
        this.model.destroy({
            success: function () {
                $(el).remove();
            }
        });
    },
    events: {
    },
    initialize: function () {
        _(this).bindAll('destroy', 'render');
    },
    render: function () {
        $('#connector-template').tmpl(this.model.toJSON()).appendTo(this.el);
        this.delegateEvents();
    }
});

Connectors.Views.List = Backbone.View.extend({
    append: function (model) {
        var p = $('<div class="row">').appendTo('#connectors'),
            view = new Connectors.Views.Edit({
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
    var collection = new Connectors.Collection();
    var view = new Connectors.Views.List({
        collection: collection
    });
    collection.fetch();
});
