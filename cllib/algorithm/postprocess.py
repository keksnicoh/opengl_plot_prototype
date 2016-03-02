#-*- coding: utf-8 -*-
"""
algorithms to map data

:author: Nicolas 'keksnicoh' Heimann 
"""
class TrackExpression():
    def __init__(self, reltive=False, smoothing=False):
        self.arguments = [
            ('sample_id', '', 'int', 'n'),
            ('record', '__global', 'float*', 'record')
        ]  

        if reltive:
            self.code = """
                if (n == 0) record[n] = {{{MAP_EXPR}}};
                else record[n] = ({{{MAP_EXPR}}})-record[0];
            """
        else:
            self.code = """record[n] = ({{{MAP_EXPR}}});"""

        if type(smoothing) is tuple:
            if smoothing[0] == 'EXP':
                alpha = str(smoothing[1])
                self.arguments.append(('smoothing', '__global', 'float*', 'smoothing'))
                self.code += """
                    if (n == 0) smoothing[0] == record[0];
                    else smoothing[n] = """+alpha+"""*record[n]+(1-"""+alpha+""")*smoothing[n-1];
                """


class ToTexture():
    def __init__(self, layout, smoothing=False, relative=False):
        self.arguments = [
            ('texture', '__write_only', 'image2d_t', 'texture')
        ]
        
        if relative:
            self.arguments += [
                ('init_texture', '__read_only', 'image2d_t', 'init_texture'),
                ('nrun', '', 'int', 'nrun'),
            ]
            self.code = """
                const sampler_t sampler = CLK_FILTER_NEAREST;
                float data = {{{MAP_EXPR}}};
                if (nrun == 0) {
                    write_imagef(texture, _FIELD, data);
                }
                else { 
                    data -= read_imagef(init_texture, sampler, _FIELD).x;
                    write_imagef(texture, _FIELD, data);
                }
            """
        else:
            self.code = """
                float data = {{{MAP_EXPR}}};
                write_imagef(texture, _FIELD, data);
            """

        if type(smoothing) == tuple:
            if smoothing[0] == 'EXP':
                if not relative:
                    self.arguments.append(('nrun', '', 'int', 'nrun'))

                if relative:
                    self.code += """if (nrun == 0) smoothing[_ELEMENTID] = 0;"""
                else:
                    self.code += """if (nrun == 0) smoothing[_ELEMENTID] = data;"""
                alpha = str(smoothing[1])
                self.code += """
                    else smoothing[_ELEMENTID] = """+alpha+"""*data+(1-"""+alpha+""")*smoothing[_ELEMENTID];
                    write_imagef(smoothing_texture, _FIELD, smoothing[_ELEMENTID]);
                """
                self.arguments += [
                    ('smoothing', '__global', 'float*', 'smoothing'),
                    ('smoothin_texture', '__write_only', 'image2d_t', 'smoothing_texture'),
                ]
        self.layout = layout
#
        #self.code = """
            #float init_variance;
#            
        #"""
        #source_expr = "{{{MAP_EXPR}}}"
        #if mean != False:
            #source_expr = "var_mean[_ELEMENTID]"
#
        #texture_write = """write_imagef(texture, _FIELD, {{{MAP_EXPR}}});""";
        #texture_init = texture_write
        #if delta_init == True:
            #texture_init = """
            #init_variance = read_imagef(init_texture, sampler, _FIELD).x;
            #write_imagef(texture, _FIELD, """+source_expr+"""-init_variance);
            #"""
#
        #if mean != False:
            #self.code += """
            #if (nrun == 0) {
                #init_variance = 0;
                #var_mean[_ELEMENTID] = 0;
                #"""+texture_write+"""
            #}
            #else { 
                #var_mean[_ELEMENTID] = float(nrun)/(nrun+1.0f)*var_mean[_ELEMENTID] 
                               #+ 1.0f/(nrun+1.0f)*({{{MAP_EXPR}}});
                #"""+texture_init+"""
            #}
        #"""
        #elif delta_init == True:
            #self.code += """
            #if (nrun == 0) {
                #init_variance = 0;
                #"""+texture_write+"""
            #}
            #else { 
                #init_variance = read_imagef(init_texture, sampler, _FIELD).x;
                #"""+texture_init+"""
            #}
        #"""
#
#            
        #mean_arguments = []
        #if mean != False:
            #mean_arguments = [
                #('nrun', '', 'int', 'nrun'),
                #('mean_buffer', 'global', 'float*', 'var_mean'),
            #]
#
        #delta_arguments = []
        #if delta_init == True:
#
            #delta_arguments = [
                #('init_texture', '__read_only', 'image2d_t', 'init_texture'),
            #]
            #if mean == False:
                #delta_arguments.insert(0, ('nrun', '', 'int', 'nrun'))
        #self.arguments = mean_arguments + delta_arguments + [
            #('texture', '__write_only', 'image2d_t', 'texture'),
        #]
        #print(self.arguments)
        #self.layout = layout

