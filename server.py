import cherrypy
import pyredstone
import json
import ast

prohibited_actions = ["_call"]

class Root:
    @cherrypy.tools.json_out(on=True)
    @cherrypy.tools.json_in(on=True, )
#    @cherrypy.tools.jsonify() 
    def index(self):
        """ Expects a JSON dict to be in cherrypy.request.json. Expected syntax of the JSON:
        {"action": "$action_name", "username": "$username", "auth_token": "$auth_token", "args": {"arg1": "arg1"...}, }
        """
        if hasattr(cherrypy.request, "json"):
            print "json", str(cherrypy.request.json), type(cherrypy.request.json), ast.literal_eval(str(cherrypy.request.json))
            data_in = ast.literal_eval(str(cherrypy.request.json))
            if "username" not in data_in or "auth_token" not in data_in:
                raise cherrypy.HTTPError(403, "Username and/or auth_token not provided.")
            if not self.client_authenticate(data_in["username"], data_in["auth_token"]):
                raise cherrypy.HTTPError(403, "Username and/or auth_token incorrect.")
            if "action" not in data_in:
                raise cherrypy.HTTPError(400, "Requests require an action.")
            if "args" not in data_in:
                args = None
            else:
                args = data_in["args"]
            # Ensure action isn"t in the prohibited list of actions, such as _call, which present a security risk.
            if data_in["action"] in prohibited_actions:
                raise cherrypy.HTTPError(405, "Action %s prohibited" % data_in["action"])
            # Try to get the function from pyredstone module. Then pass the arg list.
            try:
                methodToCall = getattr(pyredstone, data_in["action"])
                result = methodToCall(**args)
            except AttributeError as e:
                raise cherrypy.HTTPError(404, "Action not found.")
            
            print data_in
            return {"result": result}
        else:
            if pyredstone.status:
                return "Server is running."
            else:
                return "Server is not running."
    
    
    def client_authenticate(self, username, auth_token):
        return True

    @cherrypy.tools.json_out(on=True)
    @cherrypy.tools.json_in(on=True, )  
    def batch(self):
        """ Responds with JSON of the form {"action": "result", "other_action": "other_result"} """
        response = {}
        if hasattr(cherrypy.request, "json"):
            print "json", str(cherrypy.request.json), type(cherrypy.request.json), ast.literal_eval(str(cherrypy.request.json))
            data_in = ast.literal_eval(str(cherrypy.request.json))
            if "username" not in data_in or "auth_token" not in data_in:
                raise cherrypy.HTTPError(403, "Username and/or auth_token not provided.")
            if not self.client_authenticate(data_in["username"], data_in["auth_token"]):
                raise cherrypy.HTTPError(403, "Username and/or auth_token incorrect.")
            if "action_list" not in data_in:
                raise cherrypy.HTTPError(400, "Batch requests require an action_list.")
            # Process each action in action_list
            for action in data_in.items():
                # Check that each action has a command and optional arg list
                if "action" not in action:
                    raise cherrypy.HTTPError(400, "Each item in action_list needs an action.")
                if "args" not in action:
                    args = None
                else:
                    args = action["args"]
                if action["action"] in prohibited_actions:
                    raise cherrypy.HTTPError(405, "Action %s prohibited" % action["action"])
                # Try to get the function from pyredstone module. Then pass the arg list.
                try:
                    methodToCall = getattr(pyredstone, action["action"])
                    result = methodToCall(**args)
                except AttributeError as e:
                    raise cherrypy.HTTPError(404, "Action %s not found." % action["action"])
                
                response[action["action"]] = result
            print response
            return response
        else:
            if pyredstone.status:
                return "Server is running."
            else:
                return "Server is not running."
    index.exposed = True
    batch.exposed = True


cherrypy.config.update({"server.socket_host": "0.0.0.0",
                        "server.socket_port": 7777,
                       })
cherrypy.quickstart(Root())
