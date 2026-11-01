from graphitealerts.models import Graphic
from graphitealerts.orm import engine

Graphic.metadata.create_all(bind=engine)

g = Graphic()
g.id = 2
g.source = 'graphite'
g.url = 'keepLastValue(servers.zip2.put.io.system.load.load)'
g.dashboard_id = 1
g.width = 800
g.height = 600
g.from_ = '-1day'
g.ob = 1
g.title = 'foo bar baz'
g.save()
