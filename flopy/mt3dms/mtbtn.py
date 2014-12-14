import numpy as np
from numpy import empty,array
from flopy.mbase import Package
from flopy.utils import util_2d,util_3d

class Mt3dBtn(Package):
    'Basic transport package class\n'
    #--changed default ncomp to None and raise error if len(sconc) != ncomp - relieves sconc assignement problems
    def __init__(self, model, ncomp=None, mcomp=1, tunit='D', lunit='M',
                 munit='KG', prsity=0.30, icbund=1, sconc=0.0,
                 cinact=1e30, thkmin=0.01, ifmtcn=0, ifmtnp=0, 
                 ifmtrf=0, ifmtdp=0, savucn=True, nprs=0, timprs=None,
                 obs=None,nprobs=1, chkmas=True, nprmas=1, dt0=0, 
                 mxstrn=50000, ttsmult=1.0, ttsmax=0, 
                 species_names = [], extension='btn'):
        Package.__init__(self, model, extension, 'BTN', 31) 
        nrow, ncol, nlay, nper = self.parent.mf.nrow_ncol_nlay_nper
        self.heading1 = '# BTN for MT3DMS, generated by Flopy.'
        self.heading2 = '#'
        self.mcomp = mcomp
        self.tunit = tunit
        self.lunit = lunit
        self.munit = munit
        self.cinact = cinact
        self.thkmin = thkmin
        self.ifmtcn = ifmtcn
        self.ifmtnp = ifmtnp
        self.ifmtrf = ifmtrf
        self.ifmtdp = ifmtdp
        self.savucn = savucn
        self.nprs = nprs
        self.timprs = timprs
        self.obs = obs
        self.nprobs = nprobs
        self.chkmas = chkmas
        self.nprmas = nprmas
        self.species_names = species_names        
        self.prsity = util_3d(model,(nlay,nrow,ncol),np.float32,\
            prsity,name='prsity',locat=self.unit_number[0])        
        self.icbund = util_3d(model,(nlay,nrow,ncol),np.int,\
            icbund,name='icbund',locat=self.unit_number[0])
        # Starting concentrations
        #--some defense
        if np.isscalar(sconc) and ncomp is None:
            print 'setting ncomp == 1 and tiling scalar-valued sconc to nlay'
            sconc = [sconc] 
            ncomp = 1
        elif ncomp != len(sconc):
            raise Exception('BTN input error - ncomp not equal to len(sconc)')
        self.ncomp = ncomp
        self.sconc = []       
        for i in range(ncomp):
            u3d = util_3d(model,(nlay,nrow,ncol),np.float32,sconc[i],\
                name='sconc'+str(i+1),locat=self.unit_number[0])
            self.sconc.append(u3d)                    
        self.dt0 = util_2d(model,(nper,),np.float32,dt0,name='dt0')        
        self.mxstrn = util_2d(model,(nper,),np.int,mxstrn,name='mxstrn')        
        self.ttsmult = util_2d(model,(nper,),np.float32,ttsmult,name='ttmult')        
        self.ttsmax = util_2d(model,(nper,),np.float32,ttsmax,name='ttsmax')
        self.parent.add_package(self)
    def write_file(self):
        nrow, ncol, nlay, nper = self.parent.mf.nrow_ncol_nlay_nper
        ModflowDis = self.parent.mf.get_package('DIS')
        # Open file for writing
        f_btn = open(self.fn_path, 'w')
        f_btn.write('#{0:s}\n#{1:s}\n'.format(self.heading1,self.heading2))
        f_btn.write('{0:10d}{1:10d}{2:10d}{3:10d}{4:10d}{5:10d}\n'\
            .format(nlay,nrow,ncol,nper,self.ncomp,self.mcomp))
        f_btn.write('{0:4s}{1:4s}{2:4s}\n'\
            .format(self.tunit,self.lunit,self.munit))        
        if (self.parent.adv != None):         
            f_btn.write('{0:2s}'.format('T'))
        else:            
            f_btn.write('{0:2s}'.format('F'))
        if (self.parent.dsp != None):
            f_btn.write('{0:2s}'.format('T'))
        else:           
            f_btn.write('{0:2s}'.format('F'))
        if (self.parent.ssm != None):            
            f_btn.write('{0:2s}'.format('T'))
        else:
            f_btn.write('{0:2s}'.format('F'))
        if (self.parent.rct != None):            
            f_btn.write('{0:2s}'.format('T'))
        else:           
            f_btn.write('{0:2s}'.format('F'))
        if (self.parent.gcg != None):            
            f_btn.write('{0:2s}'.format('T'))
        else:            
            f_btn.write('{0:2s}'.format('F'))
        f_btn.write('\n')
        flow_package = self.parent.mf.get_package('BCF6')
        if (flow_package != None):
            lc = util_2d(self.parent,(nlay,),np.int,\
                flow_package.laycon.get_value(),name='btn - laytype',\
                locat=self.unit_number[0])
        else:
            flow_package = self.parent.mf.get_package('LPF')
            if (flow_package != None):
                lc = util_2d(self.parent,(nlay,),\
                    np.int,flow_package.laytyp.get_value(),\
                    name='btn - laytype',locat=self.unit_number[0])       
        #--need to reset lc fmtin
        lc.set_fmtin('(40I2)')
        f_btn.write(lc.string)        
        delr = util_2d(self.parent,(ncol,),\
            np.float32,ModflowDis.delr.get_value(),\
            name='delr',locat=self.unit_number[0])
        f_btn.write(delr.get_file_entry())
        
        delc = util_2d(self.parent,(nrow,),np.float32,\
            ModflowDis.delc.get_value(),name='delc',\
            locat=self.unit_number[0])
        f_btn.write(delc.get_file_entry())

        top = util_2d(self.parent,(nrow,ncol),\
            np.float32,ModflowDis.top.array,\
            name='top',locat=self.unit_number[0])
        f_btn.write(top.get_file_entry())
        
        thickness = util_3d(self.parent,(nlay,nrow,ncol),\
            np.float32,ModflowDis.thickness.get_value(),\
            name='thickness',locat=self.unit_number[0])
        f_btn.write(thickness.get_file_entry())
                
        f_btn.write(self.prsity.get_file_entry())
        
        f_btn.write(self.icbund.get_file_entry())
              
        # Starting concentrations
        for s in range(len(self.sconc)):            
            f_btn.write(self.sconc[s].get_file_entry())
               
        f_btn.write('{0:10.0E}{1:10.4f}\n'\
            .format(self.cinact,self.thkmin))
               
        f_btn.write('{0:10d}{1:10d}{2:10d}{3:10d}'\
            .format(self.ifmtcn,self.ifmtnp,self.ifmtrf,self.ifmtdp))
        if (self.savucn == True):
            ss = 'T'
        else:
            ss = 'F'        
        f_btn.write('{0:>10s}\n'.format(ss))
        
        # NPRS
        if (self.timprs == None):            
            f_btn.write('{0:10d}\n'.format(self.nprs))
        else:            
            f_btn.write('{0:10d}\n'.format(len(self.timprs)))        
            timprs = util_2d(self.parent,(len(self.timprs),)\
                ,np.int,self.timprs,name='timprs',fmtin='(8F10.0)')         
            f_btn.write(timprs.string)
        # OBS
        if (self.obs == None):            
            f_btn.write('{0:10d}{1:10d}\n'.format(0,self.nprobs))
        else:
            nobs = self.obs.shape[0]            
            f_btn.write('{0:10d}{1:10d}\n'.format(nobs,self.nprobs))
            for r in range(nobs):                
                f_btn.write('{0:10d}{1:10d}{2:10d}\n'\
                    .format(self.obs[r,0],self.obs[r,1],self.obs[r,2]))
        # CHKMAS, NPRMAS
        if (self.chkmas == True):
            ss = 'T'
        else:
            ss = 'F'        
        f_btn.write('{0:>10s}{1:10d}\n'.format(ss,self.nprmas))
        # PERLEN, NSTP, TSMULT
        for t in range(nper):            
            f_btn.write('{0:10.4g}{1:10d}{2:10f}\n'\
                .format(ModflowDis.perlen[t],ModflowDis.nstp[t],\
                ModflowDis.tsmult[t]))            
            f_btn.write('{0:10f}{1:10d}{2:10f}{3:10f}\n'\
                .format(self.dt0[t],self.mxstrn[t],\
                self.ttsmult[t],self.ttsmax[t]))
        f_btn.close() 

    @staticmethod
    def load(f, model, nlay=None, nrow=None, ncol=None, ext_unit_dict=None):
        if type(f) is not file:
            filename = f
            f = open(filename, 'r')
        #A1 and A2 
        while True:
            line = f.readline()
            if line[0] != '#':
                break
        
        a3 = line.strip().split()
        nlay,nrow,ncol,nper,ncomp,mcomp = int(a3[0]),int(a3[1]),int(a3[2]),int(a3[3]),int(a3[4]),int(a3[5])
        
        a4 = f.readline().strip().split()
        tunit,lunit,munit = a4
        
        a5 = f.readline().strip().split()

        a6 = f.readline().strip().split()


        delr = util_2d.load(f, model, (ncol,1), np.float32, 'delr',
                              ext_unit_dict)
        delc = util_2d.load(f, model, (nrow,1), np.float32, 'delc',
                              ext_unit_dict)
        htop = util_2d.load(f, model, (nrow,ncol), np.float32, 'htop',
                              ext_unit_dict)
        dz = util_3d.load(f,model,(nlay,nrow,ncol),np.float32, 'dz',
                          ext_unit_dict)
        prsity = util_3d.load(f,model,(nlay,nrow,ncol),np.float32, 'prsity',
                          ext_unit_dict)
        icbund = util_3d.load(f,model,(nlay,nrow,ncol),np.int, 'icbund',
                          ext_unit_dict)
        sconc = util_3d.load(f,model,(nlay,nrow,ncol),np.float32, 'sconc',
                          ext_unit_dict)

        a14 = f.readline().strip().split()
        cinact,thkmin = float(a14[0]),float(a14[1])

        a15 = f.readline().strip().split()
        ifmtcn,ifmtnp,ifmtrf,ifmtdp = int(a15[0]),int(a15[1]),int(a15[2]),int(a15[3])
        savucn = False
        if (a15[4].lower() == 't'): savucn = True

        a16 = f.readline().strip().split()
        nprs = int(a16[0])
        timprs = []
        while len(timprs) < nprs:
            line = f.readline().strip().split()
            [timprs.append(float(l)) for l in line]

        a18 = f.readline().strip().split()
        nobs,nprobs = int(a18[0]),int(a18[1])
        obs = []
        while len(obs) < nobs:
            line = np.array(f.readline().strip().split(),dtype=np.int)
            obs.append(line)
        obs = np.array(obs)

        a20 = f.readline().strip().split()
        chkmas = False
        if (a20[0].lower() == 't'): chkmas = True
        nprmas = int(a20[1])
        dt0,mxstrn,ttsmult,ttsmax = [],[],[],[]
        for kper in xrange(nper):
            line = f.readline().strip().split()
            tsm = float(line[2])
            if tsm <= 0:
                raise Exception("tsmult <= 0 not supported")
            line = f.readline().strip().split()

            dt0.append(float(line[0]))
            mxstrn.append(int(line[1]))
            ttsmult.append(float(line[2]))
            ttsmax.append(float(line[3]))

        f.close()
        btn = Mt3dBtn(model,ncomp=ncomp,mcomp=mcomp,tunit=tunit,lunit=lunit,\
                      munit=munit,prsity=prsity,icbund=icbund,sconc=[sconc],\
                      cinact=cinact,thkmin=thkmin,ifmtcn=ifmtcn,ifmtnp=ifmtnp,\
                      ifmtrf=ifmtrf,ifmtdp=ifmtdp,savucn=savucn,nprs=nprs,\
                      timprs=timprs,obs=obs,nprobs=nprobs,chkmas=chkmas,\
                      nprmas=nprmas,dt0=dt0,mxstrn=mxstrn,ttsmult=ttsmult,\
                      ttsmax=ttsmax)
        return btn




