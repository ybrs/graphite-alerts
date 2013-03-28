from graphitealerts.models import Graphic

Graphic.metadata.create_all()

g = Graphic()
g.id = 1
g.source = 'graphite'
g.url = 'keepLastValue(servers.*.put.io.system.load.load)'
g.dashboard_id = 1
g.width = 800
g.height = 600
g.from_ = '-1day'
g.ob = 1
g.title = 'foo bar baz'
g.save()