#!/usr/bin/env python
# -*- coding: utf-8 -*-

################################################################################
#
#	RMG Website - A Django-powered website for Reaction Mechanism Generator
#
#	Copyright (c) 2011 Prof. William H. Green (whgreen@mit.edu) and the
#	RMG Team (rmg_dev@mit.edu)
#
#	Permission is hereby granted, free of charge, to any person obtaining a
#	copy of this software and associated documentation files (the 'Software'),
#	to deal in the Software without restriction, including without limitation
#	the rights to use, copy, modify, merge, publish, distribute, sublicense,
#	and/or sell copies of the Software, and to permit persons to whom the
#	Software is furnished to do so, subject to the following conditions:
#
#	The above copyright notice and this permission notice shall be included in
#	all copies or substantial portions of the Software.
#
#	THE SOFTWARE IS PROVIDED 'AS IS', WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#	IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#	FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#	AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#	LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#	FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#	DEALINGS IN THE SOFTWARE.
#
################################################################################

from django.conf.urls.defaults import *

urlpatterns = patterns('rmgweb.database',

    # Database homepage
    (r'^$', 'views.index'),

    # Thermodynamics database
    (r'^thermo/$', 'views.thermo'),
    (r'^thermo/molecule/(?P<adjlist>[\S\s]+)$', 'views.thermoData'),
    (r'^thermo/(?P<section>\w+)/$', 'views.thermo'),
    (r'^thermo/(?P<section>\w+)/(?P<subsection>\w+)/$', 'views.thermo'),
    (r'^thermo/(?P<section>\w+)/(?P<subsection>\w+)/(?P<index>\d+).html$', 'views.thermoEntry'),

    # Kinetics database
    (r'^kinetics/$', 'views.kinetics'),
    (r'^kinetics/(?P<section>\w+)/$', 'views.kinetics'),
    (r'^kinetics/(?P<section>\w+)/(?P<subsection>\w+)/$', 'views.kinetics'),
    (r'^kinetics/(?P<section>\w+)/(?P<subsection>\w+)/(?P<index>\d+).html$', 'views.kineticsEntry'),

)
