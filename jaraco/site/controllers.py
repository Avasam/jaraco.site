import binascii
import codecs

import cherrypy
from jaraco.util import auth
import requests

from jaraco.site.charts import Charts
from jaraco.site.openid import OpenID
from jaraco.site import render, output
from jaraco.site.projecthoneypot import from_cherrypy
from . import resume

import logging
log = logging.getLogger(__name__)


class Downloader:
	@cherrypy.expose
	@output('downloader')
	def index(self):
		return render()

	@cherrypy.expose
	def download(self, name, url, submit):
		filename = name + '.mp4'
		referer = 'http://permaculture.kajabi.com/posts/earthworks-introduction'
		headers = dict(Referer=referer)
		resp = requests.get(url, stream=True, headers=headers)
		resp.raise_for_status()
		cd = 'attachment; filename="{filename}"'.format_map(locals())
		cherrypy.response.headers['Content-Disposition'] = cd
		return resp.iter_content()


class Root(object):
	charts = Charts()
	openid = OpenID()
	downloader = Downloader()

	@cherrypy.expose
	@output('welcome')
	def index(self):
		return render()

	@cherrypy.expose
	@output('project list')
	def projects(self, name=None):
		return render()

	@cherrypy.expose
	def allurbase(self):
		return str(cherrypy.request.base)

	@cherrypy.expose
	def resume(self, url=None):
		return resume.Renderer(url).html()

	@cherrypy.expose
	def resume_pdf(self, url=None):
		cherrypy.response.headers['Content-Type'] = 'application/pdf'
		return resume.Renderer(url).pdf()

	@cherrypy.expose
	def auth(self):
		return "You authenticated as %s" % cherrypy.request.login

	@cherrypy.expose
	def croakysteel_py(self):
		return from_cherrypy()


class AcctMgmt(object):
	@cherrypy.expose
	@output('Account Management')
	def index(self):
		return render()

	@cherrypy.expose
	@output('Change Password')
	def change_password(self, submit, username, old_password, new_password, new_password_confirm, system=None):
		from jaraco.site.sysadmin import NTUser
		try:
			if not new_password:
				raise ValueError("Blank passwords not allowed")
			if not new_password == new_password_confirm:
				raise ValueError("Passwords don't match")
			nt = NTUser(username, system or '.')
			nt.reset(old_password, new_password)
		except ValueError as e:
			response_messages = [
				'Password change has failed.',
				str(e),
				]
		else:
			response_messages = [
				'Password change for {nt.user.FullName} was successful!'
				.format(**vars())
			]
		return render(response_messages=response_messages)

	@cherrypy.expose
	@output('password gen')
	def password_gen(self, length=None):
		password = None

		class userstr(str): pass
		if length:
			newpass = auth.PasswordGenerator.make_password(int(length),
				encoding=None)
			password = userstr(binascii.b2a_hex(newpass))
			password.alternatives = []
			for encoding in ('base-64',):
				encoded, newlen = codecs.getencoder(encoding)(newpass)
				password.alternatives.append((encoded, encoding))
		else:
			length = 8
		return render(password=password, length=length)

class IPTool(object):
	def __init__(self):
		self.registry = dict()

	@cherrypy.expose
	def register(self, hostname, ip):
		self.registry[hostname] = ip

	@cherrypy.expose
	def report(self):
		return str(self.registry)


Root.acctmgmt = AcctMgmt()
Root.ip = IPTool()
