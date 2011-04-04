from django.http import HttpResponse

from commis.exceptions import ChefAPIError
from commis.generic_views import CommisAPIView, api
from commis.data_bag.models import DataBag, DataBagItem
from commis.db import update

class DataBagAPIView(CommisAPIView):
    model = DataBag
    item_model = DataBagItem

    def get_item_or_404(self, bag_name, name):
        bag = self.get_or_404(bag_name)
        try:
            return bag.items.get(name=name)
        except self.item_model.DoesNotExist:
            raise ChefAPIError(404, '%s %s::%s not found', self.item_model._meta.verbose_name.capitalize(), bag_name, name)

    def get_data(self, request, bag):
        data = {}
        for item in bag.items.all():
            data[item.name] = self.reverse(request, 'item_get', bag, item)
        return data

    @api('POST', admin=True)
    def item_create(self, request, name):
        if not request.json or 'id' not in request.json:
            raise ChefAPIError(500, 'No item ID specified')
        bag = self.get_or_404(name)
        if bag.items.filter(name=request.json['id']).exists():
            raise ChefAPIError(409, 'Data bag item %s::%s already exists', name, request.json['id'])
        bag.items.create(name=request.json['id'], data=request.raw_post_data)
        return request.json

    @api('GET')
    def item_get(self, request, bag_name, name):
        item = self.get_item_or_404(bag_name, name)
        return HttpResponse(item.data, status=200, content_type='application/json')

    @api('PUT', admin=True)
    def item_update(self, request, bag_name, name):
        if not request.json:
            raise ChefAPIError(500, 'No data sent')
        if request.json.get('id') != name:
            raise ChefAPIError(500, 'Name mismatch in data bag item')
        item = self.get_item_or_404(bag_name, name)
        update(item, data=request.raw_post_data)
        return HttpResponse(item.data, status=200, content_type='application/json')

    @api('DELETE', admin=True)
    def item_delete(self, request, bag_name, name):
        item = self.get_item_or_404(bag_name, name)
        item.delete()
        return HttpResponse(item.data, status=200, content_type='application/json')