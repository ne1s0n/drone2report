from jinja2 import Environment, FileSystemLoader
from datetime import date
import os
import glob

from d2r.render import Render
from d2r.misc import indexfile_to_html

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
		#a bit of interface
		self.logger.info('RENDER:' + self.to_string())
		
		#for simplicity, the jinja2 template folder goes into a local variable
		jtf = os.path.join(self.config['__d2r_basefolder'], 'jinja2_report_templates')
		
		#instantiate the auxilliary object that will take care of all operations
		report = self.__d2rReport(jtf)
		
		#adding all the found logs
		for logfile in glob.glob(self.config['logfolder'] + '/*.log'):
			#reading the log in
			with open(logfile, 'r') as file:
				log_content = file.read()
			
			#adding to the report
			report.add_section(
				"analysis_block.html",
				{"log_file": logfile, "log_content": log_content}
			)
		
		#adding the plots for all the found indexes, if required
		if self.config['index_folder'] is not None:
			for indexfile in glob.glob(self.config['index_folder'] + '/*.csv'):
				#data to html
				my_html = indexfile_to_html(indexfile)
				
				#for each combination of dataset and trait
				for key, content in my_html.items():
					#adding the title/subtitle
					report.add_section(
						"section_title.html",
						{"title": indexfile, "subtitle": key}
					)
					
					#adding the plot
					report.add_section(
						"raw_html.html",
						{"content": content}
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

	
