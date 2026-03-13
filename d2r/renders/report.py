from jinja2 import Environment, FileSystemLoader
from datetime import date
from d2r.render import Render
import os

class report(Render):
	
	"""internal class, straight from jinja2. Manages the template access,
	   exposes a minimal api for adding sections, and a render function
	   to actually save the report on disk
	"""
	class __d2rReport:
		def __init__(self, jtf):
			self.env = Environment(
				loader=FileSystemLoader([
					os.path.join(jtf, "templates"), 
					os.path.join(jtf, "sections"), 
					os.path.join(jtf, "static")
				])
			)
			self.sections = []

		def add_section(self, template_name, data):
			template = self.env.get_template(template_name)
			html = template.render(data)
			self.sections.append(html)

		def render(self, output_file, context):
			template = self.env.get_template("report.html")
			html = template.render(
				sections=self.sections,
				**context
			)
			with open(output_file, "w") as f:
				f.write(html)
	
	def run(self):
		#for simplicity, the jinja2 template folder goes into a local variable
		jtf = os.path.join(self.config['__d2r_basefolder'], 'jinja2_report_templates')
		
		#instantiate the auxilliary object that will take care of all operations
		report = self.__d2rReport(jtf)

		#adding one section for one output analysis
		report.add_section(
			"analysis_block.html",
			{"log": "Loading drone images..."}
		)

		#adding another section
		report.add_section(
			"analysis_block.html",
			{"log": "Info for new block"}
		)

		#rendering takes care also of header and footer
		report.render(
			output_file = self.config['report_file'],
			context = {
				"title": self.config['title'],
				"author": self.config['author'],
				"date": date.today()
			}
		)

		#a little interface
		print("Report generated")
		
	def parse_config(self, config):
		"""parsing config parameters specific to this subclass"""
		res = super().parse_config(config)
		#parse the res dictionary for things specific to this very subclass
		#(if any are preent)
		return(res)

