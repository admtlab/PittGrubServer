from tornado import web
import loggin

class TestHandlerAll(web.RequestHandler):
    def get(self):
        logging.info("getting all")
        value = Test.get_all()
        self.write(value.serialize())

class TestHandlerId(web.RequestHandler):
    def get(self, id):
        logging.info("getting by id: {}".format(id))
        value = Test.get_by_id(id)
        logging.info("value " + str(value))
        self.write(value.serialize())