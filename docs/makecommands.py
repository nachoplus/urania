#!/usr/bin/env python
# Describe classes, methods and functions in a module.
# Works with user-defined modules, all Python library
# modules, including built-in modules.
# http://code.activestate.com/recipes/553262-list-classes-methods-and-functions-in-a-module/

import inspect,importlib
import os, sys

INDENT=0
outputfile=sys.stdout

def wi(*args):
   """ Function to print lines indented according to level """
   
   if INDENT: outputfile.write(' '*INDENT+'\n')
   for arg in args: outputfile.write( arg+'\n')
   outputfile.write('')

def indent():
   """ Increase indentation """
   
   global INDENT
   INDENT += 4

def dedent():
   """ Decrease indentation """
   
   global INDENT
   INDENT -= 4

def describe_builtin(obj):
   """ Describe a builtin function """

   wi('+Built-in Function: %s' % obj.__name__)
   # Built-in functions cannot be inspected by
   # inspect.getargspec. We have to try and parse
   # the __doc__ attribute of the function.
   docstr = obj.__doc__
   args = ''
   
   if docstr:
      items = docstr.split('\n')
      if items:
         func_descr = items[0]
         s = func_descr.replace(obj.__name__,'')
         idx1 = s.find('(')
         idx2 = s.find(')',idx1)
         if idx1 != -1 and idx2 != -1 and (idx2>idx1+1):
            args = s[idx1+1:idx2]
            wi('\t-Method Arguments:', args)

   if args=='':
      wi('\t-Method Arguments: None')

   print
   
def describe_func(obj, method=False):
   """ Describe the function object passed as argument.
   If this is a method object, the second argument will
   be passed as True """
   
   if method:
      wi('**%s**' % obj.__name__.replace('cmd_',''))
   else:
      wi('+Function: %s' % obj.__name__)

   try:
       arginfo = inspect.getargspec(obj)
   except TypeError:
      print 
      return
   
   args = arginfo[0]
   argsvar = arginfo[1]

   if args:
       if args[0] == 'self':
           wi('\t%s' % obj.__doc__)
           args.pop(0)

       #wi('\t- Arguments:', args)

       if arginfo[3]:
           dl = len(arginfo[3])
           al = len(args)
           defargs = args[al-dl:al]
           wi('\t--Default arguments:',zip(defargs, arginfo[3]))

   if arginfo[1]:
       wi('\t-Positional Args Param: %s' % arginfo[1])
   if arginfo[2]:
       wi('\t-Keyword Args Param: %s' % arginfo[2])

   print

def describe_klass(obj):
   """ Describe the class object passed as argument,
   including its methods """
   hascmd=False
   #print obj.__dict__
   z = obj.__dict__.copy()   # start with x's keys and values
   if True:
       #look up in base class 
       try:
           z.update(obj.__base__.__dict__)
       except:
           pass
   z=sorted(z)
   for name in z:
       item = getattr(obj, name)
       if inspect.ismethod(item) and name.startswith('cmd_'):
           hascmd=True
   if hascmd:
           wi('%s commands' % obj.__name__)
           wi('^'*(len(obj.__name__)+9))
   #wi('+Class: %s' % obj.__name__)

   indent()

   count = 0

   for name in z:
       item = getattr(obj, name)
       if inspect.ismethod(item) and name.startswith('cmd_'):
           count += 1;describe_func(item, True)

   if count==0:
      pass
      #wi('(No members)')
   else:
      pass
      #wi('+Class: %s' % obj.__name__)
      
   dedent()
   print 

def describe(module):
   """ Describe the module object passed as argument
   including its classes and functions """
   
   wi('[Module: %s]\n' % module.__name__)

   indent()

   count = 0
   
   for name in dir(module):
       obj = getattr(module, name)
       if inspect.isclass(obj):
          count += 1; describe_klass(obj)
       else:
          continue
       '''
       elif (inspect.ismethod(obj) or inspect.isfunction(obj)):
          count +=1 ; describe_func(obj)
       elif inspect.isbuiltin(obj):
          count += 1; describe_builtin(obj)
       '''

   if count==0:
      wi('(No members)')
      
   #dedent()

if __name__ == "__main__":
   import sys
   
   if len(sys.argv)<2:
        p='../urania/base'
        for module in os.listdir(p):
                if module.endswith('.py') and not module.startswith('__'):
                        _module=p[3:].replace('/','.')+'.'+module.replace('.py','')
                        mod =importlib.import_module(_module)
                        outputfile=open('./source/cmd_'+module.replace('.py','.rst'),'w')
                        describe(mod)                
                        outputfile.close()

   else:
        module = sys.argv[1].replace('.py','')
        mod =importlib.import_module(module)
        describe(mod)
