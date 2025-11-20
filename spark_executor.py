import os
import sys
from io import StringIO
from contextlib import redirect_stdout, redirect_stderr
from pyspark.sql import SparkSession

class SparkExecutor:
    """Executor for running code with Apache Spark"""
    
    def __init__(self, config):
        self.config = config
        self._spark = None
    
    def get_spark_session(self):
        """Get or create Spark session"""
        if self._spark is None:
            # Handle both Config object and Flask config dict
            app_name = getattr(self.config, 'SPARK_APP_NAME', None) or self.config.get('SPARK_APP_NAME', 'OpenSourceDatabricks')
            master = getattr(self.config, 'SPARK_MASTER', None) or self.config.get('SPARK_MASTER', 'local[*]')
            
            self._spark = SparkSession.builder \
                .appName(self.config['SPARK_APP_NAME']) \
                .master(self.config['SPARK_MASTER']) \
                .config("spark.driver.memory", "2g") \
                .getOrCreate()
        return self._spark
    
    def execute_code(self, code, language='python'):
        """Execute code and return output"""
        if language != 'python':
            return {
                'success': False,
                'output': '',
                'error': f'Language {language} not supported yet'
            }
        
        try:
            # Create Spark session
            spark = self.get_spark_session()
            
            # Capture stdout and stderr
            stdout_capture = StringIO()
            stderr_capture = StringIO()
            
            # Create execution namespace with spark context
            namespace = {
                'spark': spark,
                'sc': spark.sparkContext,
                'sqlContext': spark  # sqlContext is deprecated, use spark instead
            }
            
            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                exec(code, namespace)
            
            output = stdout_capture.getvalue()
            error = stderr_capture.getvalue()
            
            return {
                'success': True,
                'output': output,
                'error': error if error else None
            }
        
        except Exception as e:
            return {
                'success': False,
                'output': '',
                'error': str(e)
            }
    
    def close(self):
        """Stop Spark session"""
        if self._spark:
            self._spark.stop()
            self._spark = None
