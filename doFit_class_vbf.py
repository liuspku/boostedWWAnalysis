#! /Usr/bin/env python
import os
import glob
import math
import array
import ROOT
import ntpath
import sys
import subprocess
from subprocess import Popen
from optparse import OptionParser

from ROOT import gROOT, TPaveLabel, gStyle, gSystem, TGaxis, TStyle, TLatex, TString, TF1,TFile,TLine, TLegend, TH1D,TH2D,THStack,TChain, TCanvas, TMatrixDSym, TMath, TText, TPad, RooFit, RooArgSet, RooArgList, RooArgSet, RooAbsData, RooAbsPdf, RooAddPdf, RooWorkspace, RooExtendPdf,RooCBShape, RooLandau, RooFFTConvPdf, RooGaussian, RooBifurGauss, RooArgusBG,RooDataSet,RooExponential,RooBreitWigner, RooVoigtian, RooNovosibirsk, RooRealVar,RooFormulaVar, RooDataHist, RooHistPdf,RooCategory, RooChebychev, RooSimultaneous, RooGenericPdf,RooConstVar, RooKeysPdf, RooHistPdf, RooEffProd, RooProdPdf, RooChi2Var, TIter, kTRUE, kFALSE, kGray, kRed, kDashed, kGreen,kAzure, kOrange, kBlack,kBlue,kYellow,kCyan, kMagenta, kWhite, TGraph, RooMCStudy

############################################
#              Job steering                #
############################################

parser = OptionParser()

parser.add_option('-a', '--additioninformation',action="store",type="string",dest="additioninformation",default="HIGGS")
parser.add_option('-b', action='store_true', dest='noX', default=False, help='no X11 windows')
parser.add_option('-c', '--channel',action="store",type="string",dest="channel",default="mu")

parser.add_option('-p', '--psmodel',action="store",type="string",dest="psmodel",default="pythia")

parser.add_option('-s','--simple', action='store_true', dest='simple', default=False, help='pre-limit in simple mode')
parser.add_option('-m','--multi', action='store_true', dest='multi', default=True, help='pre-limit in multi mode')

parser.add_option('--check', action='store_true', dest='check', default=False, help='check the workspace for limit setting')

parser.add_option('--cprime', action="store",type="int",dest="cprime",default=10)
parser.add_option('--BRnew', action="store",type="int",dest="BRnew",default=0)

parser.add_option('--closuretest', action='store',type="int", dest='closuretest', default=0, help='closure test; 0: no test; 1: A1->A2; 2: A->B')
parser.add_option('--pseudodata', action='store',type="int", dest='pseudodata', default=1, help='pseudodata 0 -> use real data, else use stack of MC backgrounds')
parser.add_option('--fitSignal', action='store',type="int", dest='fitsignal', default=0, help='fit only signal lineshape with a chosen model')

parser.add_option('--inPath', action="store",type="string",dest="inPath",default="./")

parser.add_option('--category', action="store",type="string",dest="category",default="HP")

parser.add_option('--jet_bin', action="store", type="int", dest="jet_bin", default=2)

(options, args) = parser.parse_args()

ROOT.gSystem.Load(options.inPath+"/PDFs/Util_cxx.so")
ROOT.gSystem.Load(options.inPath+"/PDFs/HWWLVJRooPdfs_cxx.so")
ROOT.gSystem.Load(options.inPath+"/PDFs/PdfDiagonalizer_cc.so")

from ROOT import draw_error_band, draw_error_band_extendPdf, draw_error_band_Decor, draw_error_band_shape_Decor, Calc_error_extendPdf, Calc_error, RooErfExpPdf, RooAlpha, RooAlpha4ErfPowPdf, RooAlpha4ErfPow2Pdf, RooAlpha4ErfPowExpPdf, PdfDiagonalizer, RooPowPdf, RooPow2Pdf, RooErfPowExpPdf, RooErfPowPdf, RooErfPow2Pdf, RooQCDPdf, RooUser1Pdf, RooBWRunPdf, RooAnaExpNPdf,RooExpNPdf, RooAlpha4ExpNPdf, RooExpTailPdf, RooAlpha4ExpTailPdf, Roo2ExpPdf, RooAlpha42ExpPdf

###############################
## doFit Class Implemetation ##
###############################

class doFit_wj_and_wlvj:

    def __init__(self, in_channel,in_higgs_sample, in_mlvj_signal_region_min=500, in_mlvj_signal_region_max=700, in_mj_min=30, in_mj_max=140, in_mlvj_min=400., in_mlvj_max=1400., fit_model="ErfExp_v1", fit_model_alter="ErfPow_v1", input_workspace=None):

            
        self.setTDRStyle();
        
        RooAbsPdf.defaultIntegratorConfig().setEpsRel(1e-9) ;
        RooAbsPdf.defaultIntegratorConfig().setEpsAbs(1e-9) ;

        ### set the channel type --> electron or muon
        self.channel = in_channel;
        self.higgs_sample = in_higgs_sample;
        if in_higgs_sample=="ggH600":  self.vbfhiggs_sample="vbfH600";
        if in_higgs_sample=="ggH700":  self.vbfhiggs_sample="vbfH700";
        if in_higgs_sample=="ggH800":  self.vbfhiggs_sample="vbfH800";
        if in_higgs_sample=="ggH900":  self.vbfhiggs_sample="vbfH900";
        if in_higgs_sample=="ggH1000": self.vbfhiggs_sample="vbfH1000";
        if in_higgs_sample=="ggH1500": self.vbfhiggs_sample="vbfH1500";
        if in_higgs_sample=="ggH2000": self.vbfhiggs_sample="vbfH2000";

        print "########################################################################################"
        print "######## define class: binning, variables, cuts, files and nuissance parameters ########"
        print "########################################################################################"

        ### Set the mj binning for plots
        self.BinWidth_mj = 5.;

        ## set the model used for the background parametrization
        self.MODEL_4_mlvj=fit_model;
        self.MODEL_4_mlvj_alter=fit_model_alter;

        ### Set the binning for mlvj plots as a function of the model
        if not options.fitsignal:
         if self.MODEL_4_mlvj=="ErfPowExp_v1" or self.MODEL_4_mlvj=="ErfPow2_v1" or self.MODEL_4_mlvj=="ErfExp_v1":
            self.BinWidth_mlvj = 35.;
         else:
            self.BinWidth_mlvj = 50.;
        else:
         if self.MODEL_4_mlvj=="ErfPowExp_v1" or self.MODEL_4_mlvj=="ErfPow2_v1" or self.MODEL_4_mlvj=="ErfExp_v1":
            self.BinWidth_mlvj = 10.;
         else:
            self.BinWidth_mlvj = 10.;

        #narrow the BinWidth_mj and BinWidth_mlvj by a factor of 5. Because Higgs-Combination-Tools will generate a binned sample, so need the bin width narrow. So, as a easy solution, we will increase the bin-width by a factor of 5 when ploting m_j m_WW

        self.leg = TLegend();
        
        self.narrow_factor = 1.;

        ## correct the binning of mj
        self.BinWidth_mj = self.BinWidth_mj/self.narrow_factor;
        nbins_mj  = int((in_mj_max-in_mj_min)/self.BinWidth_mj);
        in_mj_max = in_mj_min+nbins_mj*self.BinWidth_mj;

        ## correct the binning of mlvj
        self.BinWidth_mlvj = self.BinWidth_mlvj/self.narrow_factor;
        nbins_mlvj = int((in_mlvj_max-in_mlvj_min)/self.BinWidth_mlvj);
        in_mlvj_max = in_mlvj_min+nbins_mlvj*self.BinWidth_mlvj;

        ## define jet mass variable
        rrv_mass_j = RooRealVar("rrv_mass_j","pruned m_{J}",(in_mj_min+in_mj_max)/2.,in_mj_min,in_mj_max,"GeV/c^{2}");
        rrv_mass_j.setBins(nbins_mj);

        ## define invariant mass WW variable
        rrv_mass_lvj= RooRealVar("rrv_mass_lvj","m_{WW}",(in_mlvj_min+in_mlvj_max)/2.,in_mlvj_min,in_mlvj_max,"GeV/c^{2}");
        rrv_mass_lvj.setBins(nbins_mlvj);


        ## create the workspace and import them
        if input_workspace is None:
            self.workspace4fit_ = RooWorkspace("workspace4fit_","workspace4fit_");
        else:
            self.workspace4fit_ = input_workspace;
        getattr(self.workspace4fit_,"import")(rrv_mass_j);
        getattr(self.workspace4fit_,"import")(rrv_mass_lvj);

        #prepare workspace for unbin-Limit -> just fo the stuff on which running the limit
        self.workspace4limit_ = RooWorkspace("workspace4limit_","workspace4limit_");

        ## different code operation mode -> just normal analysis
	if options.closuretest ==0:
            self.mj_sideband_lo_min = in_mj_min;
            self.mj_sideband_lo_max = 65;
            self.mj_signal_min = 65;
            self.mj_signal_max = 105;
            self.mj_sideband_hi_min = 105;
            self.mj_sideband_hi_max = in_mj_max;
        if options.closuretest ==1: ##closure test A1->A2
            self.mj_sideband_lo_min = in_mj_min;
            self.mj_sideband_lo_max = 55;
            self.mj_signal_min = 55;
            self.mj_signal_max = 65;
            self.mj_sideband_hi_min = 105;
            self.mj_sideband_hi_max = in_mj_max;
        if options.closuretest == 2: #closure test A->B
            self.mj_sideband_lo_min = in_mj_min;
            self.mj_sideband_lo_max = 65;
            self.mj_signal_min = 100;
            self.mj_signal_max = 115;
            self.mj_sideband_hi_min = 115;
            self.mj_sideband_hi_max = in_mj_max;

        ## zone definition in the jet mass
        rrv_mass_j.setRange("sb_lo",self.mj_sideband_lo_min,self.mj_sideband_lo_max);
        rrv_mass_j.setRange("signal_region",self.mj_signal_min,self.mj_signal_max);
        rrv_mass_j.setRange("sb_hi",self.mj_sideband_hi_min,self.mj_sideband_hi_max);
        rrv_mass_j.setRange("sblo_to_sbhi",self.mj_sideband_lo_min,self.mj_sideband_hi_max);

        ## signal region definition in the mlvj variable in case of counting limit
        self.mlvj_signal_min = in_mlvj_signal_region_min
        self.mlvj_signal_max = in_mlvj_signal_region_max
        rrv_mass_lvj.setRange("signal_region",self.mlvj_signal_min,self.mlvj_signal_max);

        #prepare the data and mc files --> set the working directory and the files name
        self.file_Directory = "/gwteray/users/brianza/otrees_VBF_v6/trainingtrees_%s/"%(self.channel);

        self.PS_model = options.psmodel;

        if options.pseudodata==1:
            self.file_data = ("ofile_pseudodata.root");
        else:
            self.file_data  = ("ofile_data.root");
        self.file_ggH   = ("ofile_%s.root"%(self.higgs_sample));
        self.file_vbfH  = ("ofile_%s.root"%(self.vbfhiggs_sample));

        #WJets0 is the default PS model, WJets1 is the alternative PS model
        if self.PS_model == "pythia":
            self.file_WJets0_mc = ("ofile_WJets_exclusive_Pythia.root");
            self.file_WJets1_mc = ("ofile_WJets_Herwig.root");
        else:
            self.file_WJets0_mc = ("ofile_WJets_Herwig.root");
            self.file_WJets1_mc = ("ofile_WJets_exclusive_Pythia.root");

        self.file_VV_mc = ("ofile_VV.root");# WW+WZ
        self.file_WW_EWK_mc = ("ofile_WW2jet_phantom.root");# WW+WZ        
        self.file_TTbar_mc = ("ofile_TTbar_Powheg.root");
        self.file_TTbar_matchDn_mc = ("ofile_TTbar_matchDn.root");
        self.file_TTbar_matchUp_mc = ("ofile_TTbar_matchUp.root");
        self.file_TTbar_scaleDn_mc = ("ofile_TTbar_scaleDn.root");
        self.file_TTbar_scaleUp_mc = ("ofile_TTbar_scaleUp.root");
        self.file_TTbar_mcanlo_mc = ("ofile_TTbar_mcanlo.root");
        self.file_STop_mc     = ("ofile_STop.root");#single Top
                                                                       
        self.PS_model= options.psmodel
 
        ## event categorization as a function of the purity and the applied selection
        self.wtagger_label = options.category;

        if self.wtagger_label=="HP" :
            if self.channel=="el":
                self.wtagger_cut=0.5 ; self.wtagger_cut_min=0. ;
            if self.channel=="mu":
                self.wtagger_cut=0.5 ; self.wtagger_cut_min=0. ;
            if self.channel=="em":
                self.wtagger_cut=0.5 ; self.wtagger_cut_min=0. ;
        if self.wtagger_label=="LP":
            self.wtagger_cut=0.75 ;
            self.wtagger_cut_min=0.5 ;

        if self.wtagger_label=="nocut":
            self.wtagger_cut=10000;

        #medium wtagger_eff reweight between data and mc #Wtagger_forV SF have be add to ntuple weight;
	if self.channel=="mu" and self.wtagger_label=="HP":
          if options.pseudodata == 1:
            self.rrv_wtagger_eff_reweight_forT=RooRealVar("rrv_wtagger_eff_reweight_forT","rrv_wtagger_eff_reweight_forT",1.0);
            self.rrv_wtagger_eff_reweight_forT.setError(0.294);                        
            self.rrv_wtagger_eff_reweight_forV=RooRealVar("rrv_wtagger_eff_reweight_forV","rrv_wtagger_eff_reweight_forV",1.0);
            self.rrv_wtagger_eff_reweight_forV.setError(0.097*self.rrv_wtagger_eff_reweight_forV.getVal());
          else:
            self.rrv_wtagger_eff_reweight_forT=RooRealVar("rrv_wtagger_eff_reweight_forT","rrv_wtagger_eff_reweight_forT",1.147);
            self.rrv_wtagger_eff_reweight_forT.setError(0.294);                        
            self.rrv_wtagger_eff_reweight_forV=RooRealVar("rrv_wtagger_eff_reweight_forV","rrv_wtagger_eff_reweight_forV",0.93);
            self.rrv_wtagger_eff_reweight_forV.setError(0.097*self.rrv_wtagger_eff_reweight_forV.getVal());

        if self.channel=="el" and self.wtagger_label=="HP":
          if options.pseudodata == 1:
            self.rrv_wtagger_eff_reweight_forT=RooRealVar("rrv_wtagger_eff_reweight_forT","rrv_wtagger_eff_reweight_forT",1.0);
            self.rrv_wtagger_eff_reweight_forT.setError(0.301);            
            self.rrv_wtagger_eff_reweight_forV=RooRealVar("rrv_wtagger_eff_reweight_forV","rrv_wtagger_eff_reweight_forV",1.0);
            self.rrv_wtagger_eff_reweight_forV.setError(0.097*self.rrv_wtagger_eff_reweight_forV.getVal());
          else:
            self.rrv_wtagger_eff_reweight_forT=RooRealVar("rrv_wtagger_eff_reweight_forT","rrv_wtagger_eff_reweight_forT",1.089);
            self.rrv_wtagger_eff_reweight_forT.setError(0.301);            
            self.rrv_wtagger_eff_reweight_forV=RooRealVar("rrv_wtagger_eff_reweight_forV","rrv_wtagger_eff_reweight_forV",0.93);
            self.rrv_wtagger_eff_reweight_forV.setError(0.097*self.rrv_wtagger_eff_reweight_forV.getVal());

        if self.channel=="em" and self.wtagger_label=="HP":
          if options.pseudodata == 1:
            self.rrv_wtagger_eff_reweight_forT=RooRealVar("rrv_wtagger_eff_reweight_forT","rrv_wtagger_eff_reweight_forT", 1.0);
            self.rrv_wtagger_eff_reweight_forT.setError(0.225);
            self.rrv_wtagger_eff_reweight_forV=RooRealVar("rrv_wtagger_eff_reweight_forV","rrv_wtagger_eff_reweight_forV",1.0);
            self.rrv_wtagger_eff_reweight_forV.setError(0.097*self.rrv_wtagger_eff_reweight_forV.getVal());
          else:
            self.rrv_wtagger_eff_reweight_forT=RooRealVar("rrv_wtagger_eff_reweight_forT","rrv_wtagger_eff_reweight_forT", 1.171);
            self.rrv_wtagger_eff_reweight_forT.setError(0.225);
            self.rrv_wtagger_eff_reweight_forV=RooRealVar("rrv_wtagger_eff_reweight_forV","rrv_wtagger_eff_reweight_forV",0.93);
            self.rrv_wtagger_eff_reweight_forV.setError(0.097*self.rrv_wtagger_eff_reweight_forV.getVal());              


        if self.channel=="mu" and self.wtagger_label=="LP":
            self.rrv_wtagger_eff_reweight_forT=RooRealVar("rrv_wtagger_eff_reweight_forT","rrv_wtagger_eff_reweight_forT",1.0);
            self.rrv_wtagger_eff_reweight_forT.setError(0.048103*self.rrv_wtagger_eff_reweight_forT.getVal());
            self.rrv_wtagger_eff_reweight_forV=RooRealVar("rrv_wtagger_eff_reweight_forV","rrv_wtagger_eff_reweight_forV",1.0);
            self.rrv_wtagger_eff_reweight_forV.setError(0.097*self.rrv_wtagger_eff_reweight_forV.getVal());

        if self.channel=="el" and self.wtagger_label=="LP":
            self.rrv_wtagger_eff_reweight_forT=RooRealVar("rrv_wtagger_eff_reweight_forT","rrv_wtagger_eff_reweight_forT",1.0);
            self.rrv_wtagger_eff_reweight_forT.setError(0.08*self.rrv_wtagger_eff_reweight_forT.getVal());
            self.rrv_wtagger_eff_reweight_forV=RooRealVar("rrv_wtagger_eff_reweight_forV","rrv_wtagger_eff_reweight_forV",1.0);
            self.rrv_wtagger_eff_reweight_forV.setError(0.303);

        if self.channel=="em" and self.wtagger_label=="LP":
            self.rrv_wtagger_eff_reweight_forT=RooRealVar("rrv_wtagger_eff_reweight_forT","rrv_wtagger_eff_reweight_forT", 1.0);
            self.rrv_wtagger_eff_reweight_forT.setError(0.02*self.rrv_wtagger_eff_reweight_forT.getVal());
            self.rrv_wtagger_eff_reweight_forV=RooRealVar("rrv_wtagger_eff_reweight_forV","rrv_wtagger_eff_reweight_forV",1.0);
            self.rrv_wtagger_eff_reweight_forV.setError(0.303);


        print "wtagger efficiency correction for Top sample: %s +/- %s"%(self.rrv_wtagger_eff_reweight_forT.getVal(), self.rrv_wtagger_eff_reweight_forT.getError());
        print "wtagger efficiency correction for V sample: %s +/- %s"%(self.rrv_wtagger_eff_reweight_forV.getVal(), self.rrv_wtagger_eff_reweight_forV.getError());


        #correct the W-jet mass peak difference between data and MC
        self.mean_shift=1.0; self.sigma_scale=1.0;
#        self.mean_shift=1.4; self.sigma_scale=1.11;        
        print "mean correction for the W peak : ",self.mean_shift," Resolution correction : ",self.sigma_scale

        
        #result files: The event number, parameters and error write into a txt file. The dataset and pdfs write into a root file
        if not os.path.isdir("cards_%s"%(self.channel)): os.system("mkdir cards_%s"%(self.channel));
        self.rlt_DIR="cards_%s/"%(self.channel)

        self.file_rlt_txt                   = self.rlt_DIR+"other_hwwlvj_%s_%s_%sjet_%02d_%02d.txt"%(self.higgs_sample,self.channel,options.jet_bin,options.cprime,options.BRnew)
        self.file_rlt_root                  = self.rlt_DIR+"hwwlvj_%s_%s_%sjet_%02d_%02d_workspace.root"%(self.higgs_sample,self.channel,options.jet_bin,options.cprime,options.BRnew)
        self.file_datacard_unbin_ggHvbfH    = self.rlt_DIR+"hwwlvj_%s_%s_%sjet_%02d_%02d_unbin.txt"%(self.higgs_sample,self.channel,options.jet_bin,options.cprime,options.BRnew)
        self.file_datacard_unbin_ggH        = self.rlt_DIR+"hwwlvj_%s_%s_%sjet_ggH_%02d_%02d_unbin.txt"%(self.higgs_sample,self.channel,options.jet_bin,options.cprime,options.BRnew)
        self.file_datacard_unbin_vbfH       = self.rlt_DIR+"hwwlvj_%s_%s_%sjet_vbfH_%02d_%02d_unbin.txt"%(self.higgs_sample,self.channel,options.jet_bin,options.cprime,options.BRnew)
        self.file_datacard_counting_ggHvbfH = self.rlt_DIR+"hwwlvj_%s_%s_%sjet_%02d_%02d_counting.txt"%(self.higgs_sample,self.channel,options.jet_bin,options.cprime,options.BRnew)
        self.file_datacard_counting_ggH     = self.rlt_DIR+"hwwlvj_%s_%s_%sjet_ggH_%02d_%02d_counting.txt"%(self.higgs_sample,self.channel,options.jet_bin,options.cprime,options.BRnew)
        self.file_datacard_counting_vbfH    = self.rlt_DIR+"hwwlvj_%s_%s_%sjet_vbfH_%02d_%02d_counting.txt"%(self.higgs_sample,self.channel,options.jet_bin,options.cprime,options.BRnew)
        
        self.file_out = open(self.file_rlt_txt,"w");
        self.file_out.write("Welcome:\n");
        self.file_out.close()
        self.file_out = open(self.file_rlt_txt,"a+");

        self.higgs_xs_scale=1.0; #higgs XS scale
        
        ## color palette
        self.color_palet={ #color palet
            'data' : 1,
            'WJets' : 2,
            'VV' : 4,
            'WW_EWK' : 6,
            'STop' : 7,
            'TTbar' : 210,
            'ggH' : 1,
            'vbfH' : 12,
            'Signal': 1,
            'Uncertainty' : kBlack,
            'Other_Backgrounds' : kBlue
        }

        self.Lumi = 19297;
        if self.channel=="el":
            self.Lumi = 19166;

	#met cut:el 70; mu: 50
        self.pfMET_cut = 50;
        self.lpt_cut   = 30;
        self.vpt_cut   = 200;
        self.bcut      = 0.679;
        if self.channel=="mu":
            self.pfMET_cut = 50; 
            self.lpt_cut   = 30;        
        #deltaPhi_METj cut
        self.deltaPhi_METj_cut = 2.0;
        self.top_veto_had = 200 ;
        self.top_veto_lep = 200 ;
        self.top_veto_had_min = 150 ;
        self.top_veto_lep_min = 110 ;
        self.dEta_cut = 2.5 ;
        self.Mjj_cut  = 250 ;

        # parameters of data-driven method to get the WJets background event number.
        self.number_WJets_insideband=-1;
        self.datadriven_alpha_WJets_unbin=-1;
        self.datadriven_alpha_WJets_counting=-1;

        #uncertainty for datacard
        self.lumi_uncertainty    = 0.026;
        self.XS_STop_uncertainty = 0.30 ;
        self.XS_VV_uncertainty   = 0.30 ;
        self.XS_WW_EWK_uncertainty   = 0.30 ;        
        self.XS_TTbar_uncertainty    = 0.07 ;
        self.XS_TTbar_NLO_uncertainty = 0.063 ;# from AN-12-368 table8
        self.XS_STop_NLO_uncertainty  = 0.05 ;# from AN-12-368 table8
        self.XS_VV_NLO_uncertainty    = 0.10 ;# from AN-12-368 table8
                                                        
        self.QCDscale_ggH   = 0.0;
        self.QCDscale_ggH1in   = 0.0;
        self.QCDscale_ggH2in   = 0.19;
        
        self.QCDscale_vbfH  = 0.01;
        self.pdf_gg         = 0.0;
        self.pdf_vbf        = 0.0;
        self.hwwlnJ_pdfAcc_gg=0.03;
        self.hwwlnJ_pdfAcc_vbf=0.01;

        # from twiki https:#twiki.cern.ch/twiki/bin/view/LHCPhysics/CERNYellowReportPageAt8TeV,  
        if self.higgs_sample == "ggH600": 
            self.QCDscale_vbfH = 0.007
            self.pdf_gg        = 0.095;
            self.pdf_vbf       = 0.036
            self.hwwlnJ_pdfAcc_gg  = 0.036;
            self.hwwlnJ_pdfAcc_vbf = 0.007

        if self.higgs_sample == "ggH700": 
            self.QCDscale_vbfH = 0.008;
            self.pdf_gg        = 0.101;
            self.pdf_vbf       = 0.042
            self.hwwlnJ_pdfAcc_gg  = 0.038;
            self.hwwlnJ_pdfAcc_vbf = 0.008

        if self.higgs_sample == "ggH800": 
            self.QCDscale_vbfH = 0.010;
            self.pdf_gg        = 0.106;
            self.pdf_vbf       = 0.047;
            self.hwwlnJ_pdfAcc_gg  = 0.040;
            self.hwwlnJ_pdfAcc_vbf = 0.009

        if self.higgs_sample == "ggH900": 
            self.QCDscale_vbfH = 0.012
            self.pdf_gg        = 0.111;
            self.pdf_vbf       = 0.053
            self.hwwlnJ_pdfAcc_gg  = 0.042;
            self.hwwlnJ_pdfAcc_vbf = 0.010

        if self.higgs_sample == "ggH100": 
            self.QCDscale_vbfH = 0.013;
            self.pdf_gg        = 0.121;
            self.pdf_vbf       = 0.059; 
            self.hwwlnJ_pdfAcc_gg  = 0.046;
            self.hwwlnJ_pdfAcc_vbf = 0.011

        self.interference_ggH_uncertainty = 0.1;
        self.interference_vbfH_uncertainty = 0.5;

        #normalization uncertainty from jet scale
        self.WJets_normalization_uncertainty_from_jet_scale = 0.;        
        self.VV_normalization_uncertainty_from_jet_scale = 0.;
        self.WW_EWK_normalization_uncertainty_from_jet_scale = 0.;        
        self.STop_normalization_uncertainty_from_jet_scale = 0.;
        self.TTbar_normalization_uncertainty_from_jet_scale = 0.;
        self.ggH_normalization_uncertainty_from_jet_scale = 0.;
        self.vbf_normalization_uncertainty_from_jet_scale = 0.;

        #normalization uncertainty from lep scale
        if self.channel == "mu":
         self.WJets_normalization_uncertainty_from_lep_scale  = 1.000;        
         self.VV_normalization_uncertainty_from_lep_scale     = 1.083;
         self.WW_EWK_normalization_uncertainty_from_lep_scale = 1.008;        
         self.STop_normalization_uncertainty_from_lep_scale   = 1.000;
         self.TTbar_normalization_uncertainty_from_lep_scale  = 1.008;
         self.ggH_normalization_uncertainty_from_lep_scale    = 1.028;
         self.vbf_normalization_uncertainty_from_lep_scale    = 1.015;
        elif self.channel == "el":
         self.WJets_normalization_uncertainty_from_lep_scale  = 1.000;        
         self.VV_normalization_uncertainty_from_lep_scale     = 1.068;
         self.WW_EWK_normalization_uncertainty_from_lep_scale = 1.006;        
         self.STop_normalization_uncertainty_from_lep_scale   = 1.000;
         self.TTbar_normalization_uncertainty_from_lep_scale  = 1.000;
         self.ggH_normalization_uncertainty_from_lep_scale    = 1.014;
         self.vbf_normalization_uncertainty_from_lep_scale    = 1.004;
        elif self.channel == "em":
         self.WJets_normalization_uncertainty_from_lep_scale  = 1.000;        
         self.VV_normalization_uncertainty_from_lep_scale     = 1.075;
         self.WW_EWK_normalization_uncertainty_from_lep_scale = 1.007;        
         self.STop_normalization_uncertainty_from_lep_scale   = 1.000;
         self.TTbar_normalization_uncertainty_from_lep_scale  = 1.004;
         self.ggH_normalization_uncertainty_from_lep_scale    = 1.021;
         self.vbf_normalization_uncertainty_from_lep_scale    = 1.010;
            
        #normalization uncertainty from jet_res
        self.WJets_normalization_uncertainty_from_jet_res  = 0.;        
        self.VV_normalization_uncertainty_from_jet_res     = 0.;
        self.WW_EWK_normalization_uncertainty_from_jet_res = 0.;        
        self.STop_normalization_uncertainty_from_jet_res   = 0.;
        self.TTbar_normalization_uncertainty_from_jet_res  = 0.;
        self.ggH_normalization_uncertainty_from_jet_res    = 0.;
        self.vbf_normalization_uncertainty_from_jet_res    = 0.;        


        #normalization uncertainty from lep_res
        if self.channel == "mu":
         self.WJets_normalization_uncertainty_from_lep_res  = 1.000;        
         self.VV_normalization_uncertainty_from_lep_res     = 1.016;
         self.WW_EWK_normalization_uncertainty_from_lep_res = 1.000;        
         self.STop_normalization_uncertainty_from_lep_res   = 1.000;
         self.TTbar_normalization_uncertainty_from_lep_res  = 1.000;
         self.ggH_normalization_uncertainty_from_lep_res    = 1.001;
         self.vbf_normalization_uncertainty_from_lep_res    = 1.000;        
        elif self.channel == "el":
         self.WJets_normalization_uncertainty_from_lep_res  = 1.000;        
         self.VV_normalization_uncertainty_from_lep_res     = 1.000;
         self.WW_EWK_normalization_uncertainty_from_lep_res = 1.000;        
         self.STop_normalization_uncertainty_from_lep_res   = 1.000;
         self.TTbar_normalization_uncertainty_from_lep_res  = 1.000;
         self.ggH_normalization_uncertainty_from_lep_res    = 1.015;
         self.vbf_normalization_uncertainty_from_lep_res    = 1.001;        
        elif self.channel == "em":
         self.WJets_normalization_uncertainty_from_lep_res  = 1.000;        
         self.VV_normalization_uncertainty_from_lep_res     = 1.008;
         self.WW_EWK_normalization_uncertainty_from_lep_res = 1.000;        
         self.STop_normalization_uncertainty_from_lep_res   = 1.000;
         self.TTbar_normalization_uncertainty_from_lep_res  = 1.000;
         self.ggH_normalization_uncertainty_from_lep_res    = 1.008;
         self.vbf_normalization_uncertainty_from_lep_res    = 1.001;        
           
        #normalization uncertainty from btag
        self.WJets_normalization_uncertainty_from_btag  = 1.000;        
        self.VV_normalization_uncertainty_from_btag     = 1.006;
        self.WW_EWK_normalization_uncertainty_from_btag = 1.007;        
        self.STop_normalization_uncertainty_from_btag   = 1.033;
        self.TTbar_normalization_uncertainty_from_btag  = 1.017;
        self.ggH_normalization_uncertainty_from_btag    = 1.005;
        self.vbf_normalization_uncertainty_from_btag    = 1.002;        

        #el and mu trigger and eff uncertainty, AN2012_368_v5 12.3
        self.lep_trigger_uncertainty = 0.01;
        self.lep_eff_uncertainty     = 0.02;

        #### increase shape uncertainty
        self.shape_para_error_WJets0=1.4;
        if self.higgs_sample=="ggH600" or self.higgs_sample=="ggH700": self.shape_para_error_alpha=1.4;
        else: self.shape_para_error_alpha=2.;
        self.shape_para_error_TTbar=2.;
        
        # shape parameter uncertainty
        self.FloatingParams=RooArgList("floatpara_list");

    ## Set basic TDR style for canvas, pad ..etc ..
    def setTDRStyle(self):
        self.tdrStyle =TStyle("tdrStyle","Style for P-TDR");
        #For the canvas:
        self.tdrStyle.SetCanvasBorderMode(0);
        self.tdrStyle.SetCanvasColor(kWhite);
        self.tdrStyle.SetCanvasDefH(600); #Height of canvas
        self.tdrStyle.SetCanvasDefW(600); #Width of canvas
        self.tdrStyle.SetCanvasDefX(0); #POsition on screen
        self.tdrStyle.SetCanvasDefY(0);

        #For the Pad:
        self.tdrStyle.SetPadBorderMode(0);
        self.tdrStyle.SetPadColor(kWhite);
        self.tdrStyle.SetPadGridX(False);
        self.tdrStyle.SetPadGridY(False);
        self.tdrStyle.SetGridColor(0);
        self.tdrStyle.SetGridStyle(3);
        self.tdrStyle.SetGridWidth(1);

        #For the frame:
        self.tdrStyle.SetFrameBorderMode(0);
        self.tdrStyle.SetFrameBorderSize(1);
        self.tdrStyle.SetFrameFillColor(0);
        self.tdrStyle.SetFrameFillStyle(0);
        self.tdrStyle.SetFrameLineColor(1);
        self.tdrStyle.SetFrameLineStyle(1);
        self.tdrStyle.SetFrameLineWidth(1);

        #For the histo:
        self.tdrStyle.SetHistLineColor(1);
        self.tdrStyle.SetHistLineStyle(0);
        self.tdrStyle.SetHistLineWidth(1);
        self.tdrStyle.SetEndErrorSize(2);
        self.tdrStyle.SetErrorX(0.);
        self.tdrStyle.SetMarkerStyle(20);

        #For the fit/function:
        self.tdrStyle.SetOptFit(1);
        self.tdrStyle.SetFitFormat("5.4g");
        self.tdrStyle.SetFuncColor(2);
        self.tdrStyle.SetFuncStyle(1);
        self.tdrStyle.SetFuncWidth(1);

        #For the date:
        self.tdrStyle.SetOptDate(0);

        #For the statistics box:
        self.tdrStyle.SetOptFile(0);
        self.tdrStyle.SetOptStat(0); #To display the mean and RMS:
        self.tdrStyle.SetStatColor(kWhite);
        self.tdrStyle.SetStatFont(42);
        self.tdrStyle.SetStatFontSize(0.025);
        self.tdrStyle.SetStatTextColor(1);
        self.tdrStyle.SetStatFormat("6.4g");
        self.tdrStyle.SetStatBorderSize(1);
        self.tdrStyle.SetStatH(0.1);
        self.tdrStyle.SetStatW(0.15);

        #Margins:
        self.tdrStyle.SetPadTopMargin(0.05);
        self.tdrStyle.SetPadBottomMargin(0.13);
        self.tdrStyle.SetPadLeftMargin(0.18);
        self.tdrStyle.SetPadRightMargin(0.06);

       #For the Global title:
        self.tdrStyle.SetOptTitle(0);
        self.tdrStyle.SetTitleFont(42);
        self.tdrStyle.SetTitleColor(1);
        self.tdrStyle.SetTitleTextColor(1);
        self.tdrStyle.SetTitleFillColor(10);
        self.tdrStyle.SetTitleFontSize(0.05);

        #For the axis titles:
        self.tdrStyle.SetTitleColor(1, "XYZ");
        self.tdrStyle.SetTitleFont(42, "XYZ");
        self.tdrStyle.SetTitleSize(0.03, "XYZ");
        self.tdrStyle.SetTitleXOffset(0.9);
        self.tdrStyle.SetTitleYOffset(1.5);

        #For the axis labels:
        self.tdrStyle.SetLabelColor(1, "XYZ");
        self.tdrStyle.SetLabelFont(42, "XYZ");
        self.tdrStyle.SetLabelOffset(0.007, "XYZ");
        self.tdrStyle.SetLabelSize(0.03, "XYZ");

        #For the axis:
        self.tdrStyle.SetAxisColor(1, "XYZ");
        self.tdrStyle.SetStripDecimals(kTRUE);
        self.tdrStyle.SetTickLength(0.03, "XYZ");
        self.tdrStyle.SetNdivisions(510, "XYZ");
        self.tdrStyle.SetPadTickX(1); #To get tick marks on the opposite side of the frame
        self.tdrStyle.SetPadTickY(1);

        #Change for log plots:
        self.tdrStyle.SetOptLogx(0);
        self.tdrStyle.SetOptLogy(0);
        self.tdrStyle.SetOptLogz(0);

        #Postscript options:
        self.tdrStyle.SetPaperSize(20.,20.);
        self.tdrStyle.cd();

      
    ##################### ---------------------------------------------------
    def make_Pdf(self, label, in_model_name, mass_spectrum="_mj", ConstraintsList=[], ismc = 0):

        if TString(mass_spectrum).Contains("_mj"): rrv_x = self.workspace4fit_.var("rrv_mass_j"); 
        if TString(mass_spectrum).Contains("_mlvj"): rrv_x = self.workspace4fit_.var("rrv_mass_lvj"); 

        # W mass: 80.385
        if in_model_name == "Voig":
            print "########### Voigtian Pdf for mJ ############"
            rrv_mean_voig=RooRealVar("rrv_mean_voig"+label+"_"+self.channel+mass_spectrum,"rrv_mean_voig"+label+"_"+self.channel+mass_spectrum,84,78,88);
            rrv_width_voig=RooRealVar("rrv_width_voig"+label+"_"+self.channel+mass_spectrum,"rrv_width_voig"+label+"_"+self.channel+mass_spectrum,7.,1,40);
            rrv_sigma_voig=RooRealVar("rrv_sigma_voig"+label+"_"+self.channel+mass_spectrum,"rrv_sigma_voig"+label+"_"+self.channel+mass_spectrum,5,0.01,20);
            model_pdf = RooVoigtian("model_pdf"+label+"_"+self.channel+mass_spectrum,"model_pdf"+label+"_"+self.channel+mass_spectrum, rrv_x,rrv_mean_voig,rrv_width_voig,rrv_sigma_voig);

        # Higgs mass 600-1000
        if in_model_name == "Voig_v1":
            print "########### Voigtian Pdf for Higgs mlvj ############"
            rrv_mean_voig=RooRealVar("rrv_mean_voig"+label+"_"+self.channel+mass_spectrum,"rrv_mean_voig"+label+"_"+self.channel+mass_spectrum,650,550,1200);
            rrv_width_voig=RooRealVar("rrv_width_voig"+label+"_"+self.channel+mass_spectrum,"rrv_width_voig"+label+"_"+self.channel+mass_spectrum,100.,10,600);
            rrv_sigma_voig=RooRealVar("rrv_sigma_voig"+label+"_"+self.channel+mass_spectrum,"rrv_sigma_voig"+label+"_"+self.channel+mass_spectrum,200,10,400);
            model_pdf = RooVoigtian("model_pdf"+label+"_"+self.channel+mass_spectrum,"model_pdf"+label+"_"+self.channel+mass_spectrum, rrv_x,rrv_mean_voig,rrv_width_voig,rrv_sigma_voig);

        if in_model_name == "Voig_v2":
            label_tstring=TString(label);
            print "########### Voigtian Pdf for Higgs mlvj ############"
            if label_tstring.Contains("600") and (not label_tstring.Contains("1600") ):
             rrv_mean_voig=RooRealVar("rrv_mean_voig"+label+"_"+self.channel+"_"+self.wtagger_label+mass_spectrum,"rrv_mean_voig"+label+"_"+self.channel+"_"+self.wtagger_label+mass_spectrum,600,500,700);
             rrv_width_voig.setConstant(kTRUE);
             rrv_sigma_voig=RooRealVar("rrv_sigma_voig"+label+"_"+self.channel+"_"+self.wtagger_label+mass_spectrum,"rrv_sigma_voig"+label+"_"+self.channel+"_"+self.wtagger_label+mass_spectrum,40,10,80);

            elif label_tstring.Contains("700") and (not label_tstring.Contains("1700") ):
             rrv_mean_voig=RooRealVar("rrv_mean_voig"+label+"_"+self.channel+"_"+self.wtagger_label+mass_spectrum,"rrv_mean_voig"+label+"_"+self.channel+"_"+self.wtagger_label+mass_spectrum,700,600,800);
             rrv_width_voig=RooRealVar("rrv_width_voig"+label+"_"+self.channel+"_"+self.wtagger_label+mass_spectrum,"rrv_width_voig"+label+"_"+self.channel+"_"+self.wtagger_label+mass_spectrum,2.5,0,10);
             rrv_width_voig.setConstant(kTRUE);
             rrv_sigma_voig=RooRealVar("rrv_sigma_voig"+label+"_"+self.channel+"_"+self.wtagger_label+mass_spectrum,"rrv_sigma_voig"+label+"_"+self.channel+"_"+self.wtagger_label+mass_spectrum,40,10,80);

            elif label_tstring.Contains("800") and (not label_tstring.Contains("1800") ):
             rrv_mean_voig=RooRealVar("rrv_mean_voig"+label+"_"+self.channel+"_"+self.wtagger_label+mass_spectrum,"rrv_mean_voig"+label+"_"+self.channel+"_"+self.wtagger_label+mass_spectrum,800,700,900);
             rrv_width_voig=RooRealVar("rrv_width_voig"+label+"_"+self.channel+"_"+self.wtagger_label+mass_spectrum,"rrv_width_voig"+label+"_"+self.channel+"_"+self.wtagger_label+mass_spectrum,2.5,0,10);
             rrv_width_voig.setConstant(kTRUE);
             rrv_sigma_voig=RooRealVar("rrv_sigma_voig"+label+"_"+self.channel+"_"+self.wtagger_label+mass_spectrum,"rrv_sigma_voig"+label+"_"+self.channel+"_"+self.wtagger_label+mass_spectrum,40,10,80);

            elif label_tstring.Contains("900") and (not label_tstring.Contains("1900") ):
             rrv_mean_voig=RooRealVar("rrv_mean_voig"+label+"_"+self.channel+"_"+self.wtagger_label+mass_spectrum,"rrv_mean_voig"+label+"_"+self.channel+"_"+self.wtagger_label+mass_spectrum,900,800,1000);
             rrv_width_voig=RooRealVar("rrv_width_voig"+label+"_"+self.channel+"_"+self.wtagger_label+mass_spectrum,"rrv_width_voig"+label+"_"+self.channel+"_"+self.wtagger_label+mass_spectrum,2.5,0,10);
             rrv_width_voig.setConstant(kTRUE);
             rrv_sigma_voig=RooRealVar("rrv_sigma_voig"+label+"_"+self.channel+"_"+self.wtagger_label+mass_spectrum,"rrv_sigma_voig"+label+"_"+self.channel+"_"+self.wtagger_label+mass_spectrum,40,10,90);

            elif label_tstring.Contains("1000"):
             rrv_mean_voig=RooRealVar("rrv_mean_voig"+label+"_"+self.channel+"_"+self.wtagger_label+mass_spectrum,"rrv_mean_voig"+label+"_"+self.channel+"_"+self.wtagger_label+mass_spectrum,1000,900,1100);#
             rrv_width_voig=RooRealVar("rrv_width_voig"+label+"_"+self.channel+"_"+self.wtagger_label+mass_spectrum,"rrv_width_voig"+label+"_"+self.channel+"_"+self.wtagger_label+mass_spectrum,2.5,0,10);
             rrv_width_voig.setConstant(kTRUE);

            model_pdf = RooVoigtian("model_pdf"+label+"_"+self.channel+mass_spectrum,"model_pdf"+label+"_"+self.channel+mass_spectrum, rrv_x,rrv_mean_voig,rrv_width_voig,rrv_sigma_voig);            

        if in_model_name == "BWRUN":
            label_tstring=TString(label);
            if label_tstring.Contains("H600"):                         
                rrv_mean_BWRUN  = RooRealVar("rrv_mean_BWRUN"+label+"_"+self.channel+mass_spectrum,"rrv_mean_BWRUN"+label+"_"+self.channel+mass_spectrum,600,450,750);
                rrv_width_BWRUN = RooRealVar("rrv_width_BWRUN"+label+"_"+self.channel+mass_spectrum,"rrv_width_BWRUN"+label+"_"+self.channel+mass_spectrum,60,5,270);
            elif label_tstring.Contains("H700"):                         
                rrv_mean_BWRUN  = RooRealVar("rrv_mean_BWRUN"+label+"_"+self.channel+mass_spectrum,"rrv_mean_BWRUN"+label+"_"+self.channel+mass_spectrum,700,550,850);
                rrv_width_BWRUN = RooRealVar("rrv_width_BWRUN"+label+"_"+self.channel+mass_spectrum,"rrv_width_BWRUN"+label+"_"+self.channel+mass_spectrum,100,5,350);
            elif label_tstring.Contains("H800"):                          
                rrv_mean_BWRUN  = RooRealVar("rrv_mean_BWRUN"+label+"_"+self.channel+mass_spectrum,"rrv_mean_BWRUN"+label+"_"+self.channel+mass_spectrum,800,650,950);
                rrv_width_BWRUN = RooRealVar("rrv_width_BWRUN"+label+"_"+self.channel+mass_spectrum,"rrv_width_BWRUN"+label+"_"+self.channel+mass_spectrum,150,5,400);
            elif label_tstring.Contains("H900"):                          
                rrv_mean_BWRUN  = RooRealVar("rrv_mean_BWRUN"+label+"_"+self.channel+mass_spectrum,"rrv_mean_BWRUN"+label+"_"+self.channel+mass_spectrum,900,700,1100);
                rrv_width_BWRUN = RooRealVar("rrv_width_BWRUN"+label+"_"+self.channel+mass_spectrum,"rrv_width_BWRUN"+label+"_"+self.channel+mass_spectrum,400,70,500);
            elif label_tstring.Contains("H1000"):                         
                rrv_mean_BWRUN  = RooRealVar("rrv_mean_BWRUN"+label+"_"+self.channel+mass_spectrum,"rrv_mean_BWRUN"+label+"_"+self.channel+mass_spectrum,1000,750,1250);
                rrv_width_BWRUN = RooRealVar("rrv_width_BWRUN"+label+"_"+self.channel+mass_spectrum,"rrv_width_BWRUN"+label+"_"+self.channel+mass_spectrum,100,2,570); 

            bwrun = RooBWRunPdf("bwrun"+label+"_"+self.channel+mass_spectrum,"bwrun"+label+"_"+self.channel+mass_spectrum,rrv_x, rrv_mean_BWRUN, rrv_width_BWRUN);
            #model_pdf = RooBWRunPdf("model_pdf"+label+"_"+self.channel+mass_spectrum,"model_pdf"+label+"_"+self.channel+mass_spectrum, rrv_x, rrv_mean_BWRUN, rrv_width_BWRUN);

            rrv_mean_cb  = RooRealVar("rrv_mean_cb"+label+"_"+self.channel+mass_spectrum,"rrv_mean_cb"+label+"_"+self.channel+mass_spectrum,0);
            rrv_sigma_cb = RooRealVar("rrv_sigma_cb"+label+"_"+self.channel+mass_spectrum,"rrv_sigma_cb"+label+"_"+self.channel+mass_spectrum,50,10,300);
            cbshape      = RooGaussian("cbshape"+label+"_"+self.channel+mass_spectrum,"cbshape"+label+"_"+self.channel+mass_spectrum, rrv_x,rrv_mean_cb,rrv_sigma_cb);

            model_pdf = RooFFTConvPdf("model_pdf"+label+"_"+self.channel+mass_spectrum,"model_pdf"+label+"_"+self.channel+mass_spectrum, rrv_x, bwrun, cbshape);

 
        if in_model_name == "2Voig":
            rrv_mean_voig    = RooRealVar("rrv_mean_voig"+label+"_"+self.channel+mass_spectrum,"rrv_mean_voig"+label+"_"+self.channel+mass_spectrum,84,78,88);#W mass 80.385
            rrv_shift_2Voig  = RooRealVar("rrv_shift_2Voig"+label+"_"+self.channel+mass_spectrum,"rrv_shift_2Voig"+label+"_"+self.channel+mass_spectrum,10.8026)   # Z mass: 91.1876;  shift=91.1876-80.385=10.8026
            rrv_mean_shifted = RooFormulaVar("rrv_mean_voig2"+label+"_"+self.channel+mass_spectrum,"@0+@1",RooArgList(rrv_mean_voig,rrv_shift_2Voig));
            rrv_width_voig   = RooRealVar("rrv_width_voig"+label+"_"+self.channel+mass_spectrum,"rrv_width_voig"+label+"_"+self.channel+mass_spectrum,16.,6,26);
            rrv_sigma_voig   = RooRealVar("rrv_sigma_voig"+label+"_"+self.channel+mass_spectrum,"rrv_sigma_voig"+label+"_"+self.channel+mass_spectrum,0.);
            rrv_frac         = RooRealVar("rrv_frac"+label+"_"+self.channel+mass_spectrum,"rrv_frac"+label+"_"+self.channel+mass_spectrum,0.8,0.5,1.);
            model_voig1      = RooVoigtian("model_voig1"+label+"_"+self.channel+mass_spectrum,"model_voig1"+label+"_"+self.channel+mass_spectrum, rrv_x,rrv_mean_voig,rrv_width_voig,rrv_sigma_voig);
            model_voig2      = RooVoigtian("model_voig2"+label+"_"+self.channel+mass_spectrum,"model_voig2"+label+"_"+self.channel+mass_spectrum, rrv_x,rrv_mean_shifted,rrv_width_voig,rrv_sigma_voig);
            model_pdf = RooAddPdf("model_pdf"+label+"_"+self.channel+mass_spectrum,"model_pdf"+label+"_"+self.channel+mass_spectrum, RooArgList(model_voig1,model_voig2), RooArgList(rrv_frac));


        if in_model_name == "2Voig_v1":
            rrv_mean_voig    = RooRealVar("rrv_mean_voig"+label+"_"+self.channel+mass_spectrum,"rrv_mean_voig"+label+"_"+self.channel+mass_spectrum,800,700,900);#W mass 80.385
            rrv_shift_2Voig  = RooRealVar("rrv_shift_2Voig"+label+"_"+self.channel+mass_spectrum,"rrv_shift_2Voig"+label+"_"+self.channel+mass_spectrum,100)   # Z mass: 91.1876;  shift=91.1876-80.385=10.8026
            rrv_mean_shifted = RooFormulaVar("rrv_mean_voig2"+label+"_"+self.channel+mass_spectrum,"@0+@1",RooArgList(rrv_mean_voig,rrv_shift_2Voig));
            rrv_width_voig   = RooRealVar("rrv_width_voig"+label+"_"+self.channel+mass_spectrum,"rrv_width_voig"+label+"_"+self.channel+mass_spectrum,100.,20,200);
            rrv_sigma_voig   = RooRealVar("rrv_sigma_voig"+label+"_"+self.channel+mass_spectrum,"rrv_sigma_voig"+label+"_"+self.channel+mass_spectrum,100,20,200.);
            rrv_frac         = RooRealVar("rrv_frac"+label+"_"+self.channel,"rrv_frac"+label+"_"+self.channel,0.8,0.5,1.);
            model_voig1      = RooVoigtian("model_voig1"+label+"_"+self.channel+mass_spectrum,"model_voig1"+label+"_"+self.channel+mass_spectrum, rrv_x,rrv_mean_voig,rrv_width_voig,rrv_sigma_voig);
            model_voig2      = RooVoigtian("model_voig2"+label+"_"+self.channel+mass_spectrum,"model_voig2"+label+"_"+self.channel+mass_spectrum, rrv_x,rrv_mean_shifted,rrv_width_voig,rrv_sigma_voig);
            model_pdf        = RooAddPdf("model_pdf"+label+"_"+self.channel+mass_spectrum,"model_pdf"+label+"_"+self.channel+mass_spectrum, RooArgList(model_voig1,model_voig2), RooArgList(rrv_frac));            
    
        if in_model_name == "Gaus":
            rrv_mean_gaus  = RooRealVar("rrv_mean_gaus"+label+"_"+self.channel+mass_spectrum,"rrv_mean_gaus"+label+"_"+self.channel+mass_spectrum,84,78,88);
            rrv_sigma_gaus = RooRealVar("rrv_sigma_gaus"+label+"_"+self.channel+mass_spectrum,"rrv_sigma_gaus"+label+"_"+self.channel+mass_spectrum,7,1,15);
            model_pdf      = RooGaussian("model_pdf"+label+"_"+self.channel+mass_spectrum,"model_pdf"+label+"_"+self.channel+mass_spectrum, rrv_x,rrv_mean_gaus,rrv_sigma_gaus);

        if in_model_name == "Gaus_v1":
            label_tstring=TString(label);                        
            if label_tstring.Contains("H600"):
                rrv_mean_gaus  = RooRealVar("rrv_mean_gaus"+label+"_"+self.channel+mass_spectrum,"rrv_mean_gaus"+label+"_"+self.channel+mass_spectrum,580,550,620);
                rrv_sigma_gaus = RooRealVar("rrv_sigma_gaus"+label+"_"+self.channel+mass_spectrum,"rrv_sigma_gaus"+label+"_"+self.channel+mass_spectrum,65,40,80);
            elif label_tstring.Contains("H700"):
                rrv_mean_gaus  = RooRealVar("rrv_mean_gaus"+label+"_"+self.channel+mass_spectrum,"rrv_mean_gaus"+label+"_"+self.channel+mass_spectrum,700,650,750);
                rrv_sigma_gaus = RooRealVar("rrv_sigma_gaus"+label+"_"+self.channel+mass_spectrum,"rrv_sigma_gaus"+label+"_"+self.channel+mass_spectrum,100,40,150);
            elif label_tstring.Contains("H800"):
                rrv_mean_gaus  = RooRealVar("rrv_mean_gaus"+label+"_"+self.channel+mass_spectrum,"rrv_mean_gaus"+label+"_"+self.channel+mass_spectrum,800,750,850);
                rrv_sigma_gaus = RooRealVar("rrv_sigma_gaus"+label+"_"+self.channel+mass_spectrum,"rrv_sigma_gaus"+label+"_"+self.channel+mass_spectrum,130,120,140);
            elif label_tstring.Contains("H900"):
                rrv_mean_gaus  = RooRealVar("rrv_mean_gaus"+label+"_"+self.channel+mass_spectrum,"rrv_mean_gaus"+label+"_"+self.channel+mass_spectrum,900,850,950);
                rrv_sigma_gaus = RooRealVar("rrv_sigma_gaus"+label+"_"+self.channel+mass_spectrum,"rrv_sigma_gaus"+label+"_"+self.channel+mass_spectrum,160,10,200);
            elif label_tstring.Contains("H1000"):
                rrv_mean_gaus  = RooRealVar("rrv_mean_gaus"+label+"_"+self.channel+mass_spectrum,"rrv_mean_gaus"+label+"_"+self.channel+mass_spectrum,1000,950,1050);
                rrv_sigma_gaus = RooRealVar("rrv_sigma_gaus"+label+"_"+self.channel+mass_spectrum,"rrv_sigma_gaus"+label+"_"+self.channel+mass_spectrum,200,100,300);

            model_pdf = RooGaussian("model_pdf"+label+"_"+self.channel+mass_spectrum,"model_pdf"+label+"_"+self.channel+mass_spectrum, rrv_x,rrv_mean_gaus,rrv_sigma_gaus);
 
        if in_model_name == "BifurGaus_v1":
            label_tstring=TString(label);                        
            if label_tstring.Contains("H600"):
                rrv_mean_gaus   = RooRealVar("rrv_mean_gaus"+label+"_"+self.channel+mass_spectrum,"rrv_mean_gaus"+label+"_"+self.channel+mass_spectrum,600,450,750);
                rrv_sigma1_gaus = RooRealVar("rrv_sigma1_gaus"+label+"_"+self.channel+mass_spectrum,"rrv_sigma1_gaus"+label+"_"+self.channel+mass_spectrum,67,10,400);
                rrv_sigma2_gaus = RooRealVar("rrv_sigma2_gaus"+label+"_"+self.channel+mass_spectrum,"rrv_sigma2_gaus"+label+"_"+self.channel+mass_spectrum,67,10,400);
            elif label_tstring.Contains("H700"):
                rrv_mean_gaus   = RooRealVar("rrv_mean_gaus"+label+"_"+self.channel+mass_spectrum,"rrv_mean_gaus"+label+"_"+self.channel+mass_spectrum,700,650,750);
                rrv_sigma1_gaus = RooRealVar("rrv_sigma1_gaus"+label+"_"+self.channel+mass_spectrum,"rrv_sigma1_gaus"+label+"_"+self.channel+mass_spectrum,100,40,150);
                rrv_sigma2_gaus = RooRealVar("rrv_sigma2_gaus"+label+"_"+self.channel+mass_spectrum,"rrv_sigma2_gaus"+label+"_"+self.channel+mass_spectrum,100,40,150);
            elif label_tstring.Contains("H800"):
                rrv_mean_gaus   = RooRealVar("rrv_mean_gaus"+label+"_"+self.channel+mass_spectrum,"rrv_mean_gaus"+label+"_"+self.channel+mass_spectrum,800,700,900);
                rrv_sigma1_gaus = RooRealVar("rrv_sigma1_gaus"+label+"_"+self.channel+mass_spectrum,"rrv_sigma1_gaus"+label+"_"+self.channel+mass_spectrum,130,50,250);
                rrv_sigma2_gaus = RooRealVar("rrv_sigma2_gaus"+label+"_"+self.channel+mass_spectrum,"rrv_sigma2_gaus"+label+"_"+self.channel+mass_spectrum,130,50,250);
            elif label_tstring.Contains("H900"):
                rrv_mean_gaus   = RooRealVar("rrv_mean_gaus"+label+"_"+self.channel+mass_spectrum,"rrv_mean_gaus"+label+"_"+self.channel+mass_spectrum,900,850,900);
                rrv_sigma1_gaus = RooRealVar("rrv_sigma1_gaus"+label+"_"+self.channel+mass_spectrum,"rrv_sigma1_gaus"+label+"_"+self.channel+mass_spectrum,160,140,180);
                rrv_sigma2_gaus = RooRealVar("rrv_sigma2_gaus"+label+"_"+self.channel+mass_spectrum,"rrv_sigma2_gaus"+label+"_"+self.channel+mass_spectrum,160,140,180);
            elif label_tstring.Contains("H1000"):
                rrv_mean_gaus   = RooRealVar("rrv_mean_gaus"+label+"_"+self.channel+mass_spectrum,"rrv_mean_gaus"+label+"_"+self.channel+mass_spectrum,1000,950,1050);
                rrv_sigma1_gaus = RooRealVar("rrv_sigma1_gaus"+label+"_"+self.channel+mass_spectrum,"rrv_sigma1_gaus"+label+"_"+self.channel+mass_spectrum,200,100,300);
                rrv_sigma2_gaus = RooRealVar("rrv_sigma2_gaus"+label+"_"+self.channel+mass_spectrum,"rrv_sigma2_gaus"+label+"_"+self.channel+mass_spectrum,200,100,300);

            model_pdf = RooBifurGauss("model_pdf"+label+"_"+self.channel+mass_spectrum,"model_pdf"+label+"_"+self.channel+mass_spectrum, rrv_x,rrv_mean_gaus,rrv_sigma1_gaus,rrv_sigma2_gaus);

 
        if in_model_name == "DoubleGaus":
            label_tstring=TString(label);
            if label_tstring.Contains("H600"):             
                rrv_mean1_gaus  = RooRealVar("rrv_mean_gaus1"+label+"_"+self.channel+mass_spectrum,"rrv_mean_gaus1"+label+"_"+self.channel+mass_spectrum,650,500,750);
                rrv_mean2_gaus  = RooRealVar("rrv_mean_gaus2"+label+"_"+self.channel+mass_spectrum,"rrv_mean_gaus2"+label+"_"+self.channel+mass_spectrum,600,300,900);                
                rrv_sigma1_gaus = RooRealVar("rrv_sigma1_gaus"+label+"_"+self.channel+mass_spectrum,"rrv_sigma1_gaus"+label+"_"+self.channel+mass_spectrum,67,40,130);
                rrv_sigma2_gaus = RooRealVar("rrv_sigma2_gaus"+label+"_"+self.channel+mass_spectrum,"rrv_sigma2_gaus"+label+"_"+self.channel+mass_spectrum,150,50,400);
            elif label_tstring.Contains("H700"):             
                rrv_mean_gaus=RooRealVar("rrv_mean_gaus"+label+"_"+self.channel+mass_spectrum,"rrv_mean_gaus"+label+"_"+self.channel+mass_spectrum,700,650,750);
                rrv_sigma1_gaus=RooRealVar("rrv_sigma1_gaus"+label+"_"+self.channel+mass_spectrum,"rrv_sigma1_gaus"+label+"_"+self.channel+mass_spectrum,100,40,150);
                rrv_sigma2_gaus=RooRealVar("rrv_sigma2_gaus"+label+"_"+self.channel+mass_spectrum,"rrv_sigma2_gaus"+label+"_"+self.channel+mass_spectrum,100,40,150);
            elif label_tstring.Contains("H800"):             
                rrv_mean_gaus=RooRealVar("rrv_mean_gaus"+label+"_"+self.channel+mass_spectrum,"rrv_mean_gaus"+label+"_"+self.channel+mass_spectrum,800,700,900);
                rrv_sigma1_gaus=RooRealVar("rrv_sigma1_gaus"+label+"_"+self.channel+mass_spectrum,"rrv_sigma1_gaus"+label+"_"+self.channel+mass_spectrum,130,50,250);
                rrv_sigma2_gaus=RooRealVar("rrv_sigma2_gaus"+label+"_"+self.channel+mass_spectrum,"rrv_sigma2_gaus"+label+"_"+self.channel+mass_spectrum,130,50,250);
            elif label_tstring.Contains("H900"):             
                rrv_mean_gaus=RooRealVar("rrv_mean_gaus"+label+"_"+self.channel+mass_spectrum,"rrv_mean_gaus"+label+"_"+self.channel+mass_spectrum,900,850,900);
                rrv_sigma1_gaus=RooRealVar("rrv_sigma1_gaus"+label+"_"+self.channel+mass_spectrum,"rrv_sigma1_gaus"+label+"_"+self.channel+mass_spectrum,160,140,180);
                rrv_sigma2_gaus=RooRealVar("rrv_sigma2_gaus"+label+"_"+self.channel+mass_spectrum,"rrv_sigma2_gaus"+label+"_"+self.channel+mass_spectrum,160,140,180);
            elif label_tstring.Contains("H1000"):             
                rrv_mean_gaus=RooRealVar("rrv_mean_gaus"+label+"_"+self.channel+mass_spectrum,"rrv_mean_gaus"+label+"_"+self.channel+mass_spectrum,920,900,1000);
                rrv_sigma1_gaus=RooRealVar("rrv_sigma1_gaus"+label+"_"+self.channel+mass_spectrum,"rrv_sigma1_gaus"+label+"_"+self.channel+mass_spectrum,200,100,300);
                rrv_sigma2_gaus=RooRealVar("rrv_sigma2_gaus"+label+"_"+self.channel+mass_spectrum,"rrv_sigma2_gaus"+label+"_"+self.channel+mass_spectrum,200,100,300);

            rrv_frac  = RooRealVar("rrv_frac"+label+"_"+self.channel+mass_spectrum,"rrv_frac"+label+"_"+self.channel+mass_spectrum,0.5,0,1);    
            gaus1     = RooGaussian("gaus1"+label+"_"+self.channel+mass_spectrum,"gaus1"+label+"_"+self.channel+mass_spectrum, rrv_x,rrv_mean1_gaus,rrv_sigma1_gaus);
            gaus2     = RooGaussian("gaus2"+label+"_"+self.channel+mass_spectrum,"gaus2"+label+"_"+self.channel+mass_spectrum, rrv_x,rrv_mean2_gaus,rrv_sigma2_gaus);            
            model_pdf = RooAddPdf("model_pdf"+label+"_"+self.channel+mass_spectrum,"model_pdf"+label+"_"+self.channel+mass_spectrum,RooArgList(gaus1,gaus2),RooArgList(rrv_frac));

        if in_model_name == "Bukin":
            rrv_mean_bukin  = RooRealVar("rrv_mean_bukin"+label+"_"+self.channel+mass_spectrum,"rrv_mean_bukin"+label+"_"+self.channel+mass_spectrum,800,600,1000);
            rrv_sigma_bukin = RooRealVar("rrv_sigma_bukin"+label+"_"+self.channel+mass_spectrum,"rrv_sigma_bukin"+label+"_"+self.channel+mass_spectrum,50,10,400);
            rrv_xi_bukin    = RooRealVar("rrv_xi_bukin"+label+"_"+self.channel+mass_spectrum,"rrv_xi_bukin"+label+"_"+self.channel+mass_spectrum,0,-5,5);
            rrv_rho1_bukin  = RooRealVar("rrv_rho1_bukin"+label+"_"+self.channel+mass_spectrum,"rrv_rho1_bukin"+label+"_"+self.channel+mass_spectrum,0,-5,5);
            rrv_rho2_bukin  = RooRealVar("rrv_rho2_bukin"+label+"_"+self.channel+mass_spectrum,"rrv_rho2_bukin"+label+"_"+self.channel+mass_spectrum,0,-5,5);
            model_pdf = RooBukinPdf("model_pdf"+label+"_"+self.channel+mass_spectrum,"model_pdf"+label+"_"+self.channel+mass_spectrum, rrv_x, rrv_mean_bukin,rrv_sigma_bukin,rrv_xi_bukin,rrv_rho1_bukin,rrv_rho2_bukin);            

        if in_model_name == "Novosibirsk":
            rrv_mean_novo = RooRealVar("rrv_mean_novo"+label+"_"+self.channel+mass_spectrum,"rrv_mean_novo"+label+"_"+self.channel+mass_spectrum,500,300,700);            
            label_tstring=TString(label);
            if label_tstring.Contains("H600"):             
                rrv_mean_novo = RooRealVar("rrv_mean_novo"+label+"_"+self.channel+mass_spectrum,"rrv_mean_novo"+label+"_"+self.channel+mass_spectrum,600,400,800);
            if label_tstring.Contains("H700"):             
                rrv_mean_novo = RooRealVar("rrv_mean_novo"+label+"_"+self.channel+mass_spectrum,"rrv_mean_novo"+label+"_"+self.channel+mass_spectrum,700,500,900);                 
            if label_tstring.Contains("H800"):             
                rrv_mean_novo = RooRealVar("rrv_mean_novo"+label+"_"+self.channel+mass_spectrum,"rrv_mean_novo"+label+"_"+self.channel+mass_spectrum,800,600,1000);
            if label_tstring.Contains("H900"):             
                rrv_mean_novo = RooRealVar("rrv_mean_novo"+label+"_"+self.channel+mass_spectrum,"rrv_mean_novo"+label+"_"+self.channel+mass_spectrum,900,700,1100);                
            if label_tstring.Contains("H1000"):             
                rrv_mean_novo = RooRealVar("rrv_mean_novo"+label+"_"+self.channel+mass_spectrum,"rrv_mean_novo"+label+"_"+self.channel+mass_spectrum,1000,800,1200);                

            rrv_sigma_novo = RooRealVar("rrv_sigma_novo"+label+"_"+self.channel+mass_spectrum,"rrv_sigma_novo"+label+"_"+self.channel+mass_spectrum,50,10,400);
            rrv_alpha_novo = RooRealVar("rrv_alpha_novo"+label+"_"+self.channel+mass_spectrum,"rrv_alpha_novo"+label+"_"+self.channel+mass_spectrum,0,-5,5);

            model_pdf = RooNovosibirsk("model_pdf"+label+"_"+self.channel+mass_spectrum,"model_pdf"+label+"_"+self.channel+mass_spectrum, rrv_x, rrv_mean_novo,rrv_sigma_novo,rrv_alpha_novo);
    
        if in_model_name == "CB":
            rrv_mean_CB  = RooRealVar("rrv_mean_CB"+label+"_"+self.channel+mass_spectrum,"rrv_mean_CB"+label+"_"+self.channel+mass_spectrum,84,78,88);
            rrv_sigma_CB = RooRealVar("rrv_sigma_CB"+label+"_"+self.channel+mass_spectrum,"rrv_sigma_CB"+label+"_"+self.channel+mass_spectrum,7,4,10);
            rrv_alpha_CB = RooRealVar("rrv_alpha_CB"+label+"_"+self.channel+mass_spectrum,"rrv_alpha_CB"+label+"_"+self.channel+mass_spectrum,-2,-4,-0.5);
            rrv_n_CB     = RooRealVar("rrv_n_CB"+label+"_"+self.channel+mass_spectrum,"rrv_n_CB"+label+"_"+self.channel+mass_spectrum,2,0.,4);
            model_pdf    = RooCBShape("model_pdf"+label+"_"+self.channel+mass_spectrum,"model_pdf"+label+"_"+self.channel+mass_spectrum, rrv_x,rrv_mean_CB,rrv_sigma_CB,rrv_alpha_CB,rrv_n_CB);

        if in_model_name == "SCB_v1":
            rrv_mean_SCB   = RooRealVar("rrv_mean_SCB"+label+"_"+self.channel+mass_spectrum,"rrv_mean_SCB"+label+"_"+self.channel+mass_spectrum,800,780,820);
            rrv_sigma_SCB  = RooRealVar("rrv_sigma_SCB"+label+"_"+self.channel+mass_spectrum,"rrv_sigma_SCB"+label+"_"+self.channel+mass_spectrum,120,100,140);
            rrv_alpha1_SCB = RooRealVar("rrv_alpha1_SCB"+label+"_"+self.channel+mass_spectrum,"rrv_alpha1_SCB"+label+"_"+self.channel+mass_spectrum,-2,-4,-0.5);
            rrv_alpha2_SCB = RooRealVar("rrv_alpha2_SCB"+label+"_"+self.channel+mass_spectrum,"rrv_alpha2_SCB"+label+"_"+self.channel+mass_spectrum,2,0.5,4);
            rrv_n1_SCB     = RooRealVar("rrv_n1_SCB"+label+"_"+self.channel+mass_spectrum,"rrv_n1_SCB"+label+"_"+self.channel+mass_spectrum,2,0.,4);
            rrv_n2_SCB     = RooRealVar("rrv_n2_SCB"+label+"_"+self.channel+mass_spectrum,"rrv_n2_SCB"+label+"_"+self.channel+mass_spectrum,2,0.,4);
            frac           = RooRealVar("rrv_frac_SSCB"+label+"_"+self.channel+mass_spectrum,"rrv_frac_SSCB"+label+"_"+self.channel+mass_spectrum,0.5)
            scb1 = RooCBShape("model_pdf_scb1"+label+"_"+self.channel+mass_spectrum,"model_pdf_scb1"+label+"_"+self.channel+mass_spectrum, rrv_x,rrv_mean_SCB,rrv_sigma_SCB,rrv_alpha1_SCB,rrv_n1_SCB);
            scb2 = RooCBShape("model_pdf_scb2"+label+"_"+self.channel+mass_spectrum,"model_pdf_scb2"+label+"_"+self.channel+mass_spectrum, rrv_x,rrv_mean_SCB,rrv_sigma_SCB,rrv_alpha2_SCB,rrv_n2_SCB);
            model_pdf = RooAddPdf("model_pdf"+label+"_"+self.channel+mass_spectrum,"model_pdf"+label+"_"+self.channel+mass_spectrum,RooArgList(scb1,scb2),RooArgList(frac))

        if in_model_name == "CB_v1":
            label_tstring = TString(label);

            if label_tstring.Contains("ggH600"): 
                rrv_mean_CB  = RooRealVar("rrv_mean_CB"+label+"_"+self.channel+mass_spectrum,"rrv_mean_CB"+label+"_"+self.channel+mass_spectrum,610,580,650);
                rrv_sigma_CB = RooRealVar("rrv_sigma_CB"+label+"_"+self.channel+mass_spectrum,"rrv_sigma_CB"+label+"_"+self.channel+mass_spectrum,65,60,90);
                rrv_alpha_CB = RooRealVar("rrv_alpha_CB"+label+"_"+self.channel+mass_spectrum,"rrv_alpha_CB"+label+"_"+self.channel+mass_spectrum,-1.2,-2,-0.1);
                rrv_n_CB     = RooRealVar("rrv_n_CB"+label+"_"+self.channel+mass_spectrum,"rrv_n_CB"+label+"_"+self.channel+mass_spectrum,2.8,0.1,4);
            elif label_tstring.Contains("vbfH600"): 
                rrv_mean_CB  = RooRealVar("rrv_mean_CB"+label+"_"+self.channel+mass_spectrum,"rrv_mean_CB"+label+"_"+self.channel+mass_spectrum,600,550,650);
                rrv_sigma_CB = RooRealVar("rrv_sigma_CB"+label+"_"+self.channel+mass_spectrum,"rrv_sigma_CB"+label+"_"+self.channel+mass_spectrum,60,50,100);
                rrv_alpha_CB = RooRealVar("rrv_alpha_CB"+label+"_"+self.channel+mass_spectrum,"rrv_alpha_CB"+label+"_"+self.channel+mass_spectrum,-1,-2,-0.1);
                rrv_n_CB     = RooRealVar("rrv_n_CB"+label+"_"+self.channel+mass_spectrum,"rrv_n_CB"+label+"_"+self.channel+mass_spectrum,10,0.1,15);
            elif label_tstring.Contains("ggH700"):
                rrv_mean_CB  = RooRealVar("rrv_mean_CB"+label+"_"+self.channel+mass_spectrum,"rrv_mean_CB"+label+"_"+self.channel+mass_spectrum,700,660,740);
                rrv_sigma_CB = RooRealVar("rrv_sigma_CB"+label+"_"+self.channel+mass_spectrum,"rrv_sigma_CB"+label+"_"+self.channel+mass_spectrum,100,80,120);
                rrv_alpha_CB = RooRealVar("rrv_alpha_CB"+label+"_"+self.channel+mass_spectrum,"rrv_alpha_CB"+label+"_"+self.channel+mass_spectrum,-1.5,-2,-0.7);
                rrv_n_CB     = RooRealVar("rrv_n_CB"+label+"_"+self.channel+mass_spectrum,"rrv_n_CB"+label+"_"+self.channel+mass_spectrum,3.,1.5,5);
            elif label_tstring.Contains("vbfH700"):
                rrv_mean_CB  = RooRealVar("rrv_mean_CB"+label+"_"+self.channel+mass_spectrum,"rrv_mean_CB"+label+"_"+self.channel+mass_spectrum,700,650,750);
                rrv_sigma_CB = RooRealVar("rrv_sigma_CB"+label+"_"+self.channel+mass_spectrum,"rrv_sigma_CB"+label+"_"+self.channel+mass_spectrum,70,40,120);
                rrv_alpha_CB = RooRealVar("rrv_alpha_CB"+label+"_"+self.channel+mass_spectrum,"rrv_alpha_CB"+label+"_"+self.channel+mass_spectrum,-1,-2,-0.1);
                rrv_n_CB     = RooRealVar("rrv_n_CB"+label+"_"+self.channel+mass_spectrum,"rrv_n_CB"+label+"_"+self.channel+mass_spectrum,8.,0.1,20);
            elif label_tstring.Contains("ggH800"): 
                rrv_mean_CB  = RooRealVar("rrv_mean_CB"+label+"_"+self.channel+mass_spectrum,"rrv_mean_CB"+label+"_"+self.channel+mass_spectrum,800,750,850);
                rrv_sigma_CB = RooRealVar("rrv_sigma_CB"+label+"_"+self.channel+mass_spectrum,"rrv_sigma_CB"+label+"_"+self.channel+mass_spectrum,130,110,150);
                rrv_alpha_CB = RooRealVar("rrv_alpha_CB"+label+"_"+self.channel+mass_spectrum,"rrv_alpha_CB"+label+"_"+self.channel+mass_spectrum,-1.5,-3,-1);
                rrv_n_CB     = RooRealVar("rrv_n_CB"+label+"_"+self.channel+mass_spectrum,"rrv_n_CB"+label+"_"+self.channel+mass_spectrum,9.,2,15);
            elif label_tstring.Contains("vbfH800"): 
                rrv_mean_CB  = RooRealVar("rrv_mean_CB"+label+"_"+self.channel+mass_spectrum,"rrv_mean_CB"+label+"_"+self.channel+mass_spectrum,800,750,850);
                rrv_sigma_CB = RooRealVar("rrv_sigma_CB"+label+"_"+self.channel+mass_spectrum,"rrv_sigma_CB"+label+"_"+self.channel+mass_spectrum,90,60,150);
                rrv_alpha_CB = RooRealVar("rrv_alpha_CB"+label+"_"+self.channel+mass_spectrum,"rrv_alpha_CB"+label+"_"+self.channel+mass_spectrum,-3,-4,-1);
                rrv_n_CB     = RooRealVar("rrv_n_CB"+label+"_"+self.channel+mass_spectrum,"rrv_n_CB"+label+"_"+self.channel+mass_spectrum,8.,0.1,30);
            elif label_tstring.Contains("ggH900"):
                rrv_mean_CB  = RooRealVar("rrv_mean_CB"+label+"_"+self.channel+mass_spectrum,"rrv_mean_CB"+label+"_"+self.channel+mass_spectrum,900,800,920);
                rrv_sigma_CB = RooRealVar("rrv_sigma_CB"+label+"_"+self.channel+mass_spectrum,"rrv_sigma_CB"+label+"_"+self.channel+mass_spectrum,170,130,190);
                rrv_alpha_CB = RooRealVar("rrv_alpha_CB"+label+"_"+self.channel+mass_spectrum,"rrv_alpha_CB"+label+"_"+self.channel+mass_spectrum,-1.3,-2.5,-0.5);
                rrv_n_CB     = RooRealVar("rrv_n_CB"+label+"_"+self.channel+mass_spectrum,"rrv_n_CB"+label+"_"+self.channel+mass_spectrum,13,10,20);
            elif label_tstring.Contains("vbfH900"):
                rrv_mean_CB  = RooRealVar("rrv_mean_CB"+label+"_"+self.channel+mass_spectrum,"rrv_mean_CB"+label+"_"+self.channel+mass_spectrum,900,850,950);
                rrv_sigma_CB = RooRealVar("rrv_sigma_CB"+label+"_"+self.channel+mass_spectrum,"rrv_sigma_CB"+label+"_"+self.channel+mass_spectrum,160,140,190);
                rrv_alpha_CB = RooRealVar("rrv_alpha_CB"+label+"_"+self.channel+mass_spectrum,"rrv_alpha_CB"+label+"_"+self.channel+mass_spectrum,-1.3,-2,-0.5);
                rrv_n_CB     = RooRealVar("rrv_n_CB"+label+"_"+self.channel+mass_spectrum,"rrv_n_CB"+label+"_"+self.channel+mass_spectrum,25.,15,30);
            elif label_tstring.Contains("ggH1000"): 
                rrv_mean_CB  = RooRealVar("rrv_mean_CB"+label+"_"+self.channel+mass_spectrum,"rrv_mean_CB"+label+"_"+self.channel+mass_spectrum,1000,900,1050);
                rrv_sigma_CB = RooRealVar("rrv_sigma_CB"+label+"_"+self.channel+mass_spectrum,"rrv_sigma_CB"+label+"_"+self.channel+mass_spectrum,180,150,270);
                rrv_alpha_CB = RooRealVar("rrv_alpha_CB"+label+"_"+self.channel+mass_spectrum,"rrv_alpha_CB"+label+"_"+self.channel+mass_spectrum,-1,-3,-0.1);
                rrv_n_CB     = RooRealVar("rrv_n_CB"+label+"_"+self.channel+mass_spectrum,"rrv_n_CB"+label+"_"+self.channel+mass_spectrum,15.,10,25);
            elif label_tstring.Contains("vbfH1000"): 
                rrv_mean_CB  = RooRealVar("rrv_mean_CB"+label+"_"+self.channel+mass_spectrum,"rrv_mean_CB"+label+"_"+self.channel+mass_spectrum,1000,950,1050);
                rrv_sigma_CB = RooRealVar("rrv_sigma_CB"+label+"_"+self.channel+mass_spectrum,"rrv_sigma_CB"+label+"_"+self.channel+mass_spectrum,220,200,240);
                rrv_alpha_CB = RooRealVar("rrv_alpha_CB"+label+"_"+self.channel+mass_spectrum,"rrv_alpha_CB"+label+"_"+self.channel+mass_spectrum,-1,-3,-0.1);
                rrv_n_CB     = RooRealVar("rrv_n_CB"+label+"_"+self.channel+mass_spectrum,"rrv_n_CB"+label+"_"+self.channel+mass_spectrum,25.,15,65);

            model_pdf = RooCBShape("model_pdf"+label+"_"+self.channel+mass_spectrum,"model_pdf"+label+"_"+self.channel+mass_spectrum, rrv_x,rrv_mean_CB,rrv_sigma_CB,rrv_alpha_CB,rrv_n_CB);

        if in_model_name == "ArgusBW_v1":
            label_tstring=TString(label);
            if label_tstring.Contains("H1000"): 
                rrv_width_BW = RooRealVar("rrv_width_BW"+label+"_"+self.channel+mass_spectrum,"rrv_width_BW"+label+"_"+self.channel+mass_spectrum,100,50,600);
                rrv_m0_Argus = RooRealVar("rrv_m0_Argus"+label+"_"+self.channel+mass_spectrum,"rrv_m0_Argus"+label+"_"+self.channel+mass_spectrum, 950         );
                rrv_c_Argus  = RooRealVar("rrv_c_Argus"+label+"_"+self.channel+mass_spectrum,"rrv_c_Argus"+label+"_"+self.channel+mass_spectrum,-1,-2,-1e-1);
                rrv_frac     = RooRealVar("rrv_frac"+label+"_"+self.channel+mass_spectrum,"rrv_frac"+label+"_"+self.channel+mass_spectrum,0.5,0.0,1.);
            else:
                rrv_width_BW = RooRealVar("rrv_width_BW"+label+"_"+self.channel+mass_spectrum,"rrv_width_BW"+label+"_"+self.channel+mass_spectrum,200,50,400);
                rrv_m0_Argus = RooRealVar("rrv_m0_Argus"+label+"_"+self.channel+mass_spectrum,"rrv_m0_Argus"+label+"_"+self.channel+mass_spectrum,1000);
                rrv_c_Argus  = RooRealVar("rrv_c_Argus"+label+"_"+self.channel+mass_spectrum,"rrv_c_Argus"+label+"_"+self.channel+mass_spectrum,-1,-2,0.1);
                rrv_frac     = RooRealVar("rrv_frac"+label+"_"+self.channel+mass_spectrum,"rrv_frac"+label+"_"+self.channel+mass_spectrum,0.5,0.0,1.);
            bw = RooBreitWigner("bw"+label+"_"+self.channel+mass_spectrum,"bw"+label+"_"+self.channel+mass_spectrum, rrv_x,rrv_m0_Argus,rrv_width_BW);
            argus = RooArgusBG("argus"+label+"_"+self.channel+mass_spectrum,"argus"+label+"_"+self.channel+mass_spectrum, rrv_x, rrv_m0_Argus,rrv_c_Argus);
            model_pdf = RooAddPdf("model_pdf"+label+"_"+self.channel+mass_spectrum,"model_pdf"+label+"_"+self.channel+mass_spectrum, RooArgList(bw,argus), RooArgList(rrv_frac));
    
        if in_model_name == "CBBW": # FFT: BreitWigner*CBShape
            rrv_mean_CB  = RooRealVar("rrv_mean_CB"+label+"_"+self.channel+mass_spectrum,"rrv_mean_CB"+label+"_"+self.channel+mass_spectrum,84.0,78,88);
            rrv_sigma_CB = RooRealVar("rrv_sigma_CB"+label+"_"+self.channel+mass_spectrum,"rrv_sigma_CB"+label+"_"+self.channel+mass_spectrum,7,4,10);
            rrv_alpha_CB = RooRealVar("rrv_alpha_CB"+label+"_"+self.channel+mass_spectrum,"rrv_alpha_CB"+label+"_"+self.channel+mass_spectrum,-2,-4,-1);
            rrv_n_CB     = RooRealVar("rrv_n_CB"+label+"_"+self.channel+mass_spectrum,"rrv_n_CB"+label+"_"+self.channel+mass_spectrum,0.5,0.,2);
            rrv_mean_BW  = RooRealVar("rrv_mean_BW"+label+"_"+self.channel+mass_spectrum,"rrv_mean_BW"+label+"_"+self.channel+mass_spectrum,0);
            rrv_width_BW = RooRealVar("rrv_width_BW"+label+"_"+self.channel+mass_spectrum,"rrv_width_BW"+label+"_"+self.channel+mass_spectrum,10,5,20);

            cbshape = RooCBShape("cbshape"+label+"_"+self.channel+mass_spectrum,"cbshape"+label+"_"+self.channel+mass_spectrum, rrv_x,rrv_mean_CB,rrv_sigma_CB,rrv_alpha_CB,rrv_n_CB);
            bw      = RooBreitWigner("bw"+label+"_"+self.channel+mass_spectrum,"bw"+label+"_"+self.channel+mass_spectrum, rrv_x,rrv_mean_BW,rrv_width_BW);
            model_pdf = RooFFTConvPdf("model_pdf"+label+"_"+self.channel+mass_spectrum,"model_pdf"+label+"_"+self.channel+mass_spectrum, rrv_x, bw, cbshape);

        if in_model_name == "CBBW_v1": # FFT: BreitWigner*CBShape
            label_tstring=TString(label);
            if label_tstring.Contains("qqH800"): 
                rrv_mean_CB  = RooRealVar("rrv_mean_CB"+label+"_"+self.channel+mass_spectrum,"rrv_mean_CB"+label+"_"+self.channel+mass_spectrum,850,750,1000);
                rrv_sigma_CB = RooRealVar("rrv_sigma_CB"+label+"_"+self.channel+mass_spectrum,"rrv_sigma_CB"+label+"_"+self.channel+mass_spectrum,100,40,140);
                rrv_alpha_CB = RooRealVar("rrv_alpha_CB"+label+"_"+self.channel+mass_spectrum,"rrv_alpha_CB"+label+"_"+self.channel+mass_spectrum,-3,-5,-1);
                rrv_n_CB     = RooRealVar("rrv_n_CB"+label+"_"+self.channel+mass_spectrum,"rrv_n_CB"+label+"_"+self.channel+mass_spectrum,6,0.,11);
                rrv_mean_BW  = RooRealVar("rrv_mean_BW"+label+"_"+self.channel+mass_spectrum,"rrv_mean_BW"+label+"_"+self.channel+mass_spectrum,800);
                rrv_width_BW = RooRealVar("rrv_width_BW"+label+"_"+self.channel+mass_spectrum,"rrv_width_BW"+label+"_"+self.channel+mass_spectrum,120,40,160);
                rrv_frac     = RooRealVar("rrv_frac"+label+"_"+self.channel+mass_spectrum,"rrv_frac"+label+"_"+self.channel+mass_spectrum,0.5,0.0,1.);            
                cbshape      = RooCBShape("cbshape"+label+"_"+self.channel+mass_spectrum,"cbshape"+label+"_"+self.channel+mass_spectrum, rrv_x,rrv_mean_CB,rrv_sigma_CB,rrv_alpha_CB,rrv_n_CB);
                bw           = RooBreitWigner("bw"+label+"_"+self.channel+mass_spectrum,"bw"+label+"_"+self.channel+mass_spectrum, rrv_x,rrv_mean_BW,rrv_width_BW);
                model_pdf    = RooFFTConvPdf("model_pdf"+label+"_"+self.channel+mass_spectrum,"model_pdf"+label+"_"+self.channel+mass_spectrum,rrv_x,bw,cbshape);            
            elif label_tstring.Contains("ggH800"): 
                rrv_mean_CB  = RooRealVar("rrv_mean_CB"+label+"_"+self.channel+mass_spectrum,"rrv_mean_CB"+label+"_"+self.channel+mass_spectrum,800,750,850);
                rrv_sigma_CB = RooRealVar("rrv_sigma_CB"+label+"_"+self.channel+mass_spectrum,"rrv_sigma_CB"+label+"_"+self.channel+mass_spectrum,120,70,180);
                rrv_alpha_CB = RooRealVar("rrv_alpha_CB"+label+"_"+self.channel+mass_spectrum,"rrv_alpha_CB"+label+"_"+self.channel+mass_spectrum,-2,-5,-0.5);
                rrv_n_CB     = RooRealVar("rrv_n_CB"+label+"_"+self.channel+mass_spectrum,"rrv_n_CB"+label+"_"+self.channel+mass_spectrum,2,0.,7);
                rrv_mean_BW  = RooRealVar("rrv_mean_BW"+label+"_"+self.channel+mass_spectrum,"rrv_mean_BW"+label+"_"+self.channel+mass_spectrum,800);
                rrv_width_BW = RooRealVar("rrv_width_BW"+label+"_"+self.channel+mass_spectrum,"rrv_width_BW"+label+"_"+self.channel+mass_spectrum,100,60,160);
                rrv_frac     = RooRealVar("rrv_frac"+label+"_"+self.channel+mass_spectrum,"rrv_frac"+label+"_"+self.channel+mass_spectrum,0.5,0.0,1.);            
                cbshape      = RooCBShape("cbshape"+label+"_"+self.channel+mass_spectrum,"cbshape"+label+"_"+self.channel+mass_spectrum, rrv_x,rrv_mean_CB,rrv_sigma_CB,rrv_alpha_CB,rrv_n_CB);
                bw           = RooBreitWigner("bw"+label+"_"+self.channel+mass_spectrum,"bw"+label+"_"+self.channel+mass_spectrum, rrv_x,rrv_mean_BW,rrv_width_BW);
                model_pdf    = RooFFTConvPdf("model_pdf"+label+"_"+self.channel+mass_spectrum,"model_pdf"+label+"_"+self.channel+mass_spectrum,rrv_x,bw,cbshape);
            
        if in_model_name == "LDGaus": # FFT: Landau*Gaus            
            rrv_mean_landau  = RooRealVar("rrv_mean_landau"+label+"_"+self.channel+mass_spectrum,"rrv_mean_landau"+label+"_"+self.channel+mass_spectrum,900,700,1100);
            rrv_sigma_landau = RooRealVar("rrv_sigma_landau"+label+"_"+self.channel+mass_spectrum,"rrv_sigma_landau"+label+"_"+self.channel+mass_spectrum,100,1,200);
            rrv_mean_gaus    = RooRealVar("rrv_mean_gaus"+label+"_"+self.channel+mass_spectrum,"rrv_mean_gaus"+label+"_"+self.channel+mass_spectrum,600,500,700);
            rrv_sigma_gaus   = RooRealVar("rrv_sigma_gaus"+label+"_"+self.channel+mass_spectrum,"rrv_sigma_gaus"+label+"_"+self.channel+mass_spectrum,50,10,100);
            landau = RooLandau("landau"+label+"_"+self.channel+mass_spectrum,"landau"+label+"_"+self.channel+mass_spectrum, rrv_x,rrv_mean_landau,rrv_sigma_landau);
            gaus   = RooGaussian("gaus"+label+"_"+self.channel+mass_spectrum,"gaus"+label+"_"+self.channel+mass_spectrum, rrv_x,rrv_mean_landau,rrv_sigma_gaus);
            rrv_frac  = RooRealVar("rrv_frac"+label+"_"+self.channel+mass_spectrum,"rrv_frac"+label+"_"+self.channel+mass_spectrum,0.5,0.0,1.);
            model_pdf = RooFFTConvPdf("model_pdf"+label+"_"+self.channel+mass_spectrum,"model_pdf"+label+"_"+self.channel+mass_spectrum, rrv_x, landau, gaus);

        if in_model_name == "ExpN":
            rrv_c_ExpN = RooRealVar("rrv_c_ExpN"+label+"_"+self.channel+mass_spectrum,"rrv_c_ExpN"+label+"_"+self.channel+mass_spectrum,-3e-3,-1e-2,-1e-4);
            rrv_n_ExpN = RooRealVar("rrv_n_ExpN"+label+"_"+self.channel+mass_spectrum,"rrv_n_ExpN"+label+"_"+self.channel+mass_spectrum, 1e3, -1e4, 1e4);
            #rrv_n_ExpN = RooRealVar("rrv_n_ExpN"+label+"_"+self.channel+mass_spectrum,"rrv_n_ExpN"+label+"_"+self.channel+mass_spectrum, 1e3, 0, 1e4);
            model_pdf = ROOT.RooExpNPdf("model_pdf"+label+"_"+self.channel+mass_spectrum,"model_pdf"+label+"_"+self.channel+mass_spectrum,rrv_x,rrv_c_ExpN, rrv_n_ExpN);
            #model_pdf = ROOT.RooAnaExpNPdf("model_pdf"+label+"_"+self.channel+mass_spectrum,"model_pdf"+label+"_"+self.channel+mass_spectrum,rrv_x,rrv_c_ExpN, rrv_n_ExpN);


        if in_model_name == "ExpTail":
            rrv_s_ExpTail = RooRealVar("rrv_s_ExpTail"+label+"_"+self.channel+mass_spectrum,"rrv_s_ExpTail"+label+"_"+self.channel+mass_spectrum, 170,50,300);
            rrv_a_ExpTail = RooRealVar("rrv_a_ExpTail"+label+"_"+self.channel+mass_spectrum,"rrv_a_ExpTail"+label+"_"+self.channel+mass_spectrum, 3e-2,0,7e-2);
            model_pdf = ROOT.RooExpTailPdf("model_pdf"+label+"_"+self.channel+mass_spectrum,"model_pdf"+label+"_"+self.channel+mass_spectrum,rrv_x,rrv_s_ExpTail, rrv_a_ExpTail);

        if in_model_name == "2Exp":
            rrv_c0_2Exp = RooRealVar("rrv_c0_2Exp"+label+"_"+self.channel+mass_spectrum,"rrv_c0_2Exp"+label+"_"+self.channel+mass_spectrum, -5e-3, -8e-3,-4e-3);
            rrv_c1_2Exp = RooRealVar("rrv_c1_2Exp"+label+"_"+self.channel+mass_spectrum,"rrv_c1_2Exp"+label+"_"+self.channel+mass_spectrum, -1e-3, -4e-3,-1e-4);
            rrv_frac_2Exp = RooRealVar("rrv_frac_2Exp"+label+"_"+self.channel+mass_spectrum,"rrv_frac_2Exp"+label+"_"+self.channel+mass_spectrum, 0., 0., 1e-2);
            model_pdf = ROOT.Roo2ExpPdf("model_pdf"+label+"_"+self.channel+mass_spectrum,"model_pdf"+label+"_"+self.channel+mass_spectrum,rrv_x,rrv_c0_2Exp,rrv_c1_2Exp,rrv_frac);

        if( in_model_name == "Exp" or in_model_name == "Exp_sr"):            
            rrv_c_Exp = RooRealVar("rrv_c_Exp"+label+"_"+self.channel+mass_spectrum,"rrv_c_Exp"+label+"_"+self.channel+mass_spectrum,-0.05,-0.1,0.);
            model_pdf = ROOT.RooExponential("model_pdf"+label+"_"+self.channel+mass_spectrum,"model_pdf"+label+"_"+self.channel+mass_spectrum,rrv_x,rrv_c_Exp);

        if in_model_name == "ErfExp" :
            rrv_c_ErfExp      = RooRealVar("rrv_c_ErfExp"+label+"_"+self.channel+mass_spectrum,"rrv_c_ErfExp"+label+"_"+self.channel+mass_spectrum,-0.05,-0.5,-1e-4);
            rrv_offset_ErfExp = RooRealVar("rrv_offset_ErfExp"+label+"_"+self.channel+mass_spectrum,"rrv_offset_ErfExp"+label+"_"+self.channel+mass_spectrum,60.,30.,200);
            rrv_width_ErfExp  = RooRealVar("rrv_width_ErfExp"+label+"_"+self.channel+mass_spectrum,"rrv_width_ErfExp"+label+"_"+self.channel+mass_spectrum,30.)#,10, 80.);
            model_pdf = ROOT.RooErfExpPdf("model_pdf"+label+"_"+self.channel+mass_spectrum,"model_pdf"+label+"_"+self.channel+mass_spectrum,rrv_x,rrv_c_ErfExp,rrv_offset_ErfExp,rrv_width_ErfExp);


        if in_model_name == "ErfExp_v1" : #different init-value and range
            rrv_c_ErfExp      = RooRealVar("rrv_c_ErfExp"+label+"_"+self.channel+mass_spectrum,"rrv_c_ErfExp"+label+"_"+self.channel+mass_spectrum,-0.006,-0.1,0.);
            rrv_offset_ErfExp = RooRealVar("rrv_offset_ErfExp"+label+"_"+self.channel+mass_spectrum,"rrv_offset_ErfExp"+label+"_"+self.channel+mass_spectrum,450.,400.,550.);            
            label_tstring=TString(label);
            if label_tstring.Contains("H600"):             
                rrv_offset_ErfExp = RooRealVar("rrv_offset_ErfExp"+label+"_"+self.channel+mass_spectrum,"rrv_offset_ErfExp"+label+"_"+self.channel+mass_spectrum,600.,400.,800.);
            elif label_tstring.Contains("H700"):
                rrv_offset_ErfExp = RooRealVar("rrv_offset_ErfExp"+label+"_"+self.channel+mass_spectrum,"rrv_offset_ErfExp"+label+"_"+self.channel+mass_spectrum,700.,500.,900.);
            elif label_tstring.Contains("H800"):
                rrv_offset_ErfExp = RooRealVar("rrv_offset_ErfExp"+label+"_"+self.channel+mass_spectrum,"rrv_offset_ErfExp"+label+"_"+self.channel+mass_spectrum,800.,600.,1000.);
            elif label_tstring.Contains("H900"):
                rrv_offset_ErfExp = RooRealVar("rrv_offset_ErfExp"+label+"_"+self.channel+mass_spectrum,"rrv_offset_ErfExp"+label+"_"+self.channel+mass_spectrum,900.,700.,1100.);
            elif label_tstring.Contains("H1000"):
                rrv_offset_ErfExp = RooRealVar("rrv_offset_ErfExp"+label+"_"+self.channel+mass_spectrum,"rrv_offset_ErfExp"+label+"_"+self.channel+mass_spectrum,1000.,800.,1150.);       

            rrv_width_ErfExp = RooRealVar("rrv_width_ErfExp"+label+"_"+self.channel+mass_spectrum,"rrv_width_ErfExp"+label+"_"+self.channel+mass_spectrum,70.,15.,100.);
            model_pdf        = ROOT.RooErfExpPdf("model_pdf"+label+"_"+self.channel+mass_spectrum,"model_pdf"+label+"_"+self.channel+mass_spectrum,rrv_x,rrv_c_ErfExp,rrv_offset_ErfExp,rrv_width_ErfExp);


        if in_model_name == "ErfExp_v2" : #different init-value and range
            rrv_c_ErfExp       = RooRealVar("rrv_c_ErfExp"+label+"_"+self.channel+mass_spectrum,"rrv_c_ErfExp"+label+"_"+self.channel+mass_spectrum,-0.005,-0.1,0.);
            rrv_offset_ErfExp  = RooRealVar("rrv_offset_ErfExp"+label+"_"+self.channel+mass_spectrum,"rrv_offset_ErfExp"+label+"_"+self.channel+mass_spectrum,450.,400.,500.);
            rrv_width_ErfExp   = RooRealVar("rrv_width_ErfExp"+label+"_"+self.channel+mass_spectrum,"rrv_width_ErfExp"+label+"_"+self.channel+mass_spectrum, 50.,10,100.);
            rrv_residue_ErfExp = RooRealVar("rrv_residue_ErfExp"+label+"_"+self.channel+mass_spectrum,"rrv_residue_ErfExp"+label+"_"+self.channel+mass_spectrum,0.,0.,1.);

            model_pdf = RooGenericPdf("model_pdf"+label+"_"+self.channel+mass_spectrum,"model_pdf"+label+"_"+self.channel+mass_spectrum, "(TMath::Exp(%s*%s) + %s)*(1.+TMath::Erf((%s-%s)/%s))/2. "%(rrv_c_ErfExp.GetName(),rrv_x.GetName(), rrv_residue_ErfExp.GetName(), rrv_x.GetName(),rrv_offset_ErfExp.GetName(), rrv_width_ErfExp.GetName()), RooArgList(rrv_x,rrv_c_ErfExp,rrv_offset_ErfExp,rrv_width_ErfExp,rrv_residue_ErfExp) )

        if in_model_name == "ErfExp_v3" : #different init-value and range
            rrv_c_ErfExp       = RooRealVar("rrv_c_ErfExp"+label+"_"+self.channel+mass_spectrum,"rrv_c_ErfExp"+label+"_"+self.channel+mass_spectrum,-0.005,-0.1,0.);
            rrv_offset_ErfExp  = RooRealVar("rrv_offset_ErfExp"+label+"_"+self.channel+mass_spectrum,"rrv_offset_ErfExp"+label+"_"+self.channel+mass_spectrum,450.,400,500.);
            rrv_width_ErfExp   = RooRealVar("rrv_width_ErfExp"+label+"_"+self.channel+mass_spectrum,"rrv_width_ErfExp"+label+"_"+self.channel+mass_spectrum, 50.,10,100.);
            rrv_residue_ErfExp = RooRealVar("rrv_residue_ErfExp"+label+"_"+self.channel+mass_spectrum,"rrv_residue_ErfExp"+label+"_"+self.channel+mass_spectrum,0.,0.,1.);
            rrv_high_ErfExp    = RooRealVar("rrv_high_ErfExp"+label+"_"+self.channel+mass_spectrum,"rrv_high_ErfExp"+label+"_"+self.channel+mass_spectrum,1.,0.,400);
            rrv_high_ErfExp.setConstant(kTRUE);
            model_pdf = RooGenericPdf("model_pdf"+label+"_"+self.channel+mass_spectrum,"model_pdf"+label+"_"+self.channel+mass_spectrum, "(TMath::Exp(%s*%s) + %s)* TMath::Power( ((1+TMath::Erf((%s-%s)/%s))/2.), %s )"%(rrv_c_ErfExp.GetName(),rrv_x.GetName(), rrv_residue_ErfExp.GetName(),rrv_x.GetName(),rrv_offset_ErfExp.GetName(), rrv_width_ErfExp.GetName(), rrv_high_ErfExp.GetName()), RooArgList(rrv_x,rrv_c_ErfExp,rrv_offset_ErfExp,rrv_high_ErfExp,rrv_width_ErfExp,rrv_residue_ErfExp) )
      
            
        if in_model_name == "ErfExpGaus":
            rrv_c_ErfExp      = RooRealVar("rrv_c_ErfExp"+label+"_"+self.channel+mass_spectrum,"rrv_c_ErfExp"+label+"_"+self.channel+mass_spectrum,-0.05,-0.4,0.);
            rrv_offset_ErfExp = RooRealVar("rrv_offset_ErfExp"+label+"_"+self.channel+mass_spectrum,"rrv_offset_ErfExp"+label+"_"+self.channel+mass_spectrum,100.,10.,300.);
            rrv_width_ErfExp  = RooRealVar("rrv_width_ErfExp"+label+"_"+self.channel+mass_spectrum,"rrv_width_ErfExp"+label+"_"+self.channel+mass_spectrum,30.,10,100.);

            erfExp = ROOT.RooErfExpPdf("erfExp"+label+"_"+self.channel+mass_spectrum,"erfExp"+label+"_"+self.channel+mass_spectrum,rrv_x,rrv_c_ErfExp,rrv_offset_ErfExp,rrv_width_ErfExp);

            rrv_mean_gaus     = RooRealVar("rrv_mean_gaus"+label+"_"+self.channel+mass_spectrum,"rrv_mean_gaus"+label+"_"+self.channel+mass_spectrum,82,70,87);
            rrv_sigma_gaus    = RooRealVar("rrv_sigma_gaus"+label+"_"+self.channel+mass_spectrum,"rrv_sigma_gaus"+label+"_"+self.channel+mass_spectrum,7,4,15);
            rrv_high          = RooRealVar("rrv_high"+label+"_"+self.channel+mass_spectrum,"rrv_high"+label+"_"+self.channel+mass_spectrum,0.7,0.,1.);

            gaus = RooGaussian("gaus"+label+"_"+self.channel+mass_spectrum,"gaus"+label+"_"+self.channel+mass_spectrum, rrv_x,rrv_mean_gaus,rrv_sigma_gaus);

            model_pdf =RooAddPdf("model_pdf"+label+"_"+self.channel+mass_spectrum,"model_pdf"+label+"_"+self.channel+mass_spectrum,RooArgList(erfExp,gaus),RooArgList(rrv_high))

        if in_model_name == "ErfExpGaus_sp":#offset == mean
            rrv_c_ErfExp     = RooRealVar("rrv_c_ErfExp"+label+"_"+self.channel+mass_spectrum,"rrv_c_ErfExp"+label+"_"+self.channel+mass_spectrum,-0.05,-0.2,0.);
            rrv_width_ErfExp = RooRealVar("rrv_width_ErfExp"+label+"_"+self.channel+mass_spectrum,"rrv_width_ErfExp"+label+"_"+self.channel+mass_spectrum,30.,10.,200.);
            rrv_mean1_gaus  = RooRealVar("rrv_mean1_gaus"+label+"_"+self.channel+mass_spectrum,"rrv_mean1_gaus"+label+"_"+self.channel+mass_spectrum,84,78,88);

            erfExp = ROOT.RooErfExpPdf("erfExp"+label+"_"+self.channel+mass_spectrum,"erfExp"+label+"_"+self.channel+mass_spectrum,rrv_x,rrv_c_ErfExp,rrv_mean1_gaus,rrv_width_ErfExp);

            rrv_sigma1_gaus = RooRealVar("rrv_sigma1_gaus"+label+"_"+self.channel+mass_spectrum,"rrv_sigma1_gaus"+label+"_"+self.channel+mass_spectrum,7,4,10);
            rrv_high = RooRealVar("rrv_high"+label+"_"+self.channel+mass_spectrum,"rrv_high"+label+"_"+self.channel+mass_spectrum,0.5,0.,1.);

            gaus = RooGaussian("gaus"+label+"_"+self.channel+mass_spectrum,"gaus"+label+"_"+self.channel+mass_spectrum, rrv_x,rrv_mean1_gaus,rrv_sigma1_gaus);
            model_pdf = RooAddPdf("model_pdf"+label+"_"+self.channel+mass_spectrum,"model_pdf"+label+"_"+self.channel+mass_spectrum,RooArgList(erfExp,gaus),RooArgList(rrv_high))


        if in_model_name == "ErfExpGaus_v0":
            rrv_c_ErfExp      = RooRealVar("rrv_c_ErfExp"+label+"_"+self.channel+mass_spectrum,"rrv_c_ErfExp"+label+"_"+self.channel+mass_spectrum,-0.05,-0.2,0.);
            rrv_offset_ErfExp = RooRealVar("rrv_offset_ErfExp"+label+"_"+self.channel+mass_spectrum,"rrv_offset_ErfExp"+label+"_"+self.channel+mass_spectrum,100.,10.,140.);
            rrv_width_ErfExp  = RooRealVar("rrv_width_ErfExp"+label+"_"+self.channel+mass_spectrum,"rrv_width_ErfExp"+label+"_"+self.channel+mass_spectrum,30.,10,100.);

            erfExp = ROOT.RooErfExpPdf("erfExp"+label+"_"+self.channel+mass_spectrum,"erfExp"+label+"_"+self.channel+mass_spectrum,rrv_x,rrv_c_ErfExp,rrv_offset_ErfExp,rrv_width_ErfExp);

            rrv_mean_gaus  = RooRealVar("rrv_mean_gaus"+label+"_"+self.channel+mass_spectrum,"rrv_mean_gaus"+label+"_"+self.channel+mass_spectrum,84,78,88);
            rrv_sigma_gaus = RooRealVar("rrv_sigma_gaus"+label+"_"+self.channel+mass_spectrum,"rrv_sigma_gaus"+label+"_"+self.channel+mass_spectrum,7,4,10);
            rrv_high = RooRealVar("rrv_high"+label+"_"+self.channel+mass_spectrum,"rrv_high"+label+"_"+self.channel+mass_spectrum,0.7,0.,1.);

            gaus = RooGaussian("gaus"+label+"_"+self.channel+mass_spectrum,"gaus"+label+"_"+self.channel+mass_spectrum, rrv_x,rrv_mean_gaus,rrv_sigma_gaus);

            model_pdf =RooAddPdf("model_pdf"+label+"_"+self.channel+mass_spectrum,"model_pdf"+label+"_"+self.channel+mass_spectrum,RooArgList(erfExp,gaus),RooArgList(rrv_high))
    
        if in_model_name == "ErfExpGaus_v1":

            rrv_c_ErfExp      = RooRealVar("rrv_c_ErfExp"+label+"_"+self.channel+mass_spectrum,"rrv_c_ErfExp"+label+"_"+self.channel+mass_spectrum,-0.007,-0.1,0.);
            rrv_offset_ErfExp = RooRealVar("rrv_offset_ErfExp"+label+"_"+self.channel+mass_spectrum,"rrv_offset_ErfExp"+label+"_"+self.channel+mass_spectrum,800.,10.,1400.);
            rrv_width_ErfExp  = RooRealVar("rrv_width_ErfExp"+label+"_"+self.channel+mass_spectrum,"rrv_width_ErfExp"+label+"_"+self.channel+mass_spectrum,24.,10,150.);

            erfExp = ROOT.RooErfExpPdf("erfExp"+label+"_"+self.channel+mass_spectrum,"erfExp"+label+"_"+self.channel+mass_spectrum,rrv_x,rrv_c_ErfExp,rrv_offset_ErfExp,rrv_width_ErfExp);

            rrv_mean_gaus  = RooRealVar("rrv_mean_gaus"+label+"_"+self.channel+mass_spectrum,"rrv_mean_gaus"+label+"_"+self.channel+mass_spectrum,700,500,1200);
            rrv_sigma_gaus = RooRealVar("rrv_sigma_gaus"+label+"_"+self.channel+mass_spectrum,"rrv_sigma_gaus"+label+"_"+self.channel+mass_spectrum,150,10,300);
            rrv_high       = RooRealVar("rrv_high"+label+"_"+self.channel+mass_spectrum,"rrv_high"+label+"_"+self.channel+mass_spectrum,0.1,0.,1.);

            gaus = RooGaussian("gaus"+label+"_"+self.channel+mass_spectrum,"gaus"+label+"_"+self.channel+mass_spectrum, rrv_x,rrv_mean_gaus,rrv_sigma_gaus);

            model_pdf =RooAddPdf("model_pdf"+label+"_"+self.channel+mass_spectrum,"model_pdf"+label+"_"+self.channel+mass_spectrum,RooArgList(erfExp,gaus),RooArgList(rrv_high))

    
        if in_model_name == "ErfExpGaus_v2":
            rrv_c_ErfExp      = RooRealVar("rrv_c_ErfExp"+label+"_"+self.channel+mass_spectrum,"rrv_c_ErfExp"+label+"_"+self.channel+mass_spectrum,-0.05,-10.,0.);
            rrv_offset_ErfExp = RooRealVar("rrv_offset_ErfExp"+label+"_"+self.channel+mass_spectrum,"rrv_offset_ErfExp"+label+"_"+self.channel+mass_spectrum,100.,10.,140.);
            rrv_width_ErfExp  = RooRealVar("rrv_width_ErfExp"+label+"_"+self.channel+mass_spectrum,"rrv_width_ErfExp"+label+"_"+self.channel+mass_spectrum,30.,10,100.);
            rrv_mean_gaus     = RooRealVar("rrv_mean_gaus"+label+"_"+self.channel+mass_spectrum,"rrv_mean_gaus"+label+"_"+self.channel+mass_spectrum,84,78,88);
            rrv_sigma_gaus    = RooRealVar("rrv_sigma_gaus"+label+"_"+self.channel+mass_spectrum,"rrv_sigma_gaus"+label+"_"+self.channel+mass_spectrum,7,4,10);
            rrv_high  = RooRealVar("rrv_high"+label+"_"+self.channel+mass_spectrum,"rrv_high"+label+"_"+self.channel+mass_spectrum,200.,0.,1000.);
            model_pdf = ROOT.RooErfExp_Gaus_Pdf("model_pdf"+label+"_"+self.channel+mass_spectrum,"model_pdf"+label+"_"+self.channel+mass_spectrum, rrv_x,rrv_c_ErfExp,rrv_offset_ErfExp,rrv_width_ErfExp,rrv_mean_gaus,rrv_sigma_gaus,rrv_high );
    
        if in_model_name == "ErfExp2Gaus":
            rrv_c_ErfExp      = RooRealVar("rrv_c_ErfExp"+label+"_"+self.channel+mass_spectrum,"rrv_c_ErfExp"+label+"_"+self.channel+mass_spectrum,-0.05,-0.2,0.);
            rrv_offset_ErfExp = RooRealVar("rrv_offset_ErfExp"+label+"_"+self.channel+mass_spectrum,"rrv_offset_ErfExp"+label+"_"+self.channel+mass_spectrum,100.,10.,240.);
            rrv_width_ErfExp  = RooRealVar("rrv_width_ErfExp"+label+"_"+self.channel+mass_spectrum,"rrv_width_ErfExp"+label+"_"+self.channel+mass_spectrum,30.,10,200.);

            erfExp = ROOT.RooErfExpPdf("erfExp"+label+"_"+self.channel+mass_spectrum,"erfExp"+label+"_"+self.channel+mass_spectrum,rrv_x,rrv_c_ErfExp,rrv_offset_ErfExp,rrv_width_ErfExp);

            rrv_mean1_gaus  = RooRealVar("rrv_mean1_gaus"+label+"_"+self.channel+mass_spectrum,"rrv_mean1_gaus"+label+"_"+self.channel+mass_spectrum,84,78,88);
            rrv_mean2_gaus  = RooRealVar("rrv_mean2_gaus"+label+"_"+self.channel+mass_spectrum,"rrv_mean2_gaus"+label+"_"+self.channel+mass_spectrum,180,170,190);
            rrv_sigma1_gaus = RooRealVar("rrv_sigma1_gaus"+label+"_"+self.channel+mass_spectrum,"rrv_sigma1_gaus"+label+"_"+self.channel+mass_spectrum,7,4,10);
            rrv_sigma2_gaus = RooRealVar("rrv_sigma2_gaus"+label+"_"+self.channel+mass_spectrum,"rrv_sigma2_gaus"+label+"_"+self.channel+mass_spectrum,10,2,25);
            rrv_high1 = RooRealVar("rrv_high1"+label+"_"+self.channel+mass_spectrum,"rrv_high1"+label+"_"+self.channel+mass_spectrum,0.6,0.,1.);
            rrv_high2 = RooRealVar("rrv_high2"+label+"_"+self.channel+mass_spectrum,"rrv_high2"+label+"_"+self.channel+mass_spectrum,0.4,0.,1.);

            gaus1 = RooGaussian("gaus1"+label+"_"+self.channel+mass_spectrum,"gaus1"+label+"_"+self.channel+mass_spectrum, rrv_x,rrv_mean1_gaus,rrv_sigma1_gaus);
            gaus2 = RooGaussian("gaus2"+label+"_"+self.channel+mass_spectrum,"gaus2"+label+"_"+self.channel+mass_spectrum, rrv_x,rrv_mean2_gaus,rrv_sigma2_gaus);

            model_pdf =RooAddPdf("model_pdf"+label+"_"+self.channel+mass_spectrum,"model_pdf"+label+"_"+self.channel+mass_spectrum,RooArgList(erfExp,gaus1,gaus2),RooArgList(rrv_high1,rrv_high2))

        if in_model_name == "2Gaus":

            mean1_tmp     =8.3145e+01;  mean1_tmp_err     =1.63e-01;
            deltamean_tmp =6.6321e+00;  deltamean_tmp_err =1.21e+00;
            sigma1_tmp    =7.5097e+00;  sigma1_tmp_err    =2.01e-01;
            scalesigma_tmp=3.8707e+00;  scalesigma_tmp_err=2.20e-01;
            frac_tmp      =6.4728e-01;  frac_tmp_err      =2.03e-02; 

            if self.wtagger_cut==0.43:
                mean1_tmp     =8.3089e+01;  mean1_tmp_err     =1.61e-01;
                deltamean_tmp =9.3065e+00;  deltamean_tmp_err =1.67e+00;
                sigma1_tmp    =7.5280e+00;  sigma1_tmp_err    =1.91e-01;
                scalesigma_tmp=3.4619e+00;  scalesigma_tmp_err=2.29e-01;
                frac_tmp      =7.4246e-01;  frac_tmp_err      =2.11e-02; 

            if self.wtagger_cut==0.50:
                mean1_tmp     =8.3141e+01;  mean1_tmp_err     =1.63e-01;
                deltamean_tmp =6.9129e+00;  deltamean_tmp_err =1.24e+00;
                sigma1_tmp    =7.5145e+00;  sigma1_tmp_err    =1.99e-01;
                scalesigma_tmp=3.6819e+00;  scalesigma_tmp_err=2.11e-01;
                frac_tmp      =6.7125e-01;  frac_tmp_err      =2.09e-02; 


            rrv_mean1_gaus  = RooRealVar("rrv_mean1_gaus"+label+"_"+self.channel+mass_spectrum,"rrv_mean1_gaus"+label+"_"+self.channel+mass_spectrum,mean1_tmp, mean1_tmp-4, mean1_tmp+4);
            rrv_sigma1_gaus = RooRealVar("rrv_sigma1_gaus"+label+"_"+self.channel+mass_spectrum,"rrv_sigma1_gaus"+label+"_"+self.channel+mass_spectrum,sigma1_tmp, sigma1_tmp-4,sigma1_tmp+4 );
            gaus1 = RooGaussian("gaus1"+label+"_"+self.channel+mass_spectrum,"gaus1"+label+"_"+self.channel+mass_spectrum, rrv_x,rrv_mean1_gaus,rrv_sigma1_gaus);

            rrv_deltamean_gaus = RooRealVar("rrv_deltamean_gaus"+label+"_"+self.channel+mass_spectrum,"rrv_deltamean_gaus"+label+"_"+self.channel+mass_spectrum,deltamean_tmp, -4, deltamean_tmp+deltamean_tmp_err*4);
            rrv_mean2_gaus     = RooFormulaVar("rrv_mean2_gaus"+label+"_"+self.channel+mass_spectrum,"@0+@1",RooArgList(rrv_mean1_gaus, rrv_deltamean_gaus));
            rrv_scalesigma_gaus = RooRealVar("rrv_scalesigma_gaus"+label+"_"+self.channel+mass_spectrum,"rrv_scalesigma_gaus"+label+"_"+self.channel+mass_spectrum,scalesigma_tmp, scalesigma_tmp-scalesigma_tmp_err*8, scalesigma_tmp+scalesigma_tmp_err*8); 
            rrv_sigma2_gaus = RooFormulaVar("rrv_sigma2_gaus"+label+"_"+self.channel+mass_spectrum,"@0*@1", RooArgList(rrv_sigma1_gaus,rrv_scalesigma_gaus));
            gaus2 = RooGaussian("gaus2"+label+"_"+self.channel+mass_spectrum,"gaus2"+label+"_"+self.channel+mass_spectrum, rrv_x,rrv_mean2_gaus,rrv_sigma2_gaus);

            rrv_frac = RooRealVar("rrv_frac"+label+"_"+self.channel+mass_spectrum,"rrv_frac"+label+"_"+self.channel+mass_spectrum,frac_tmp, frac_tmp-frac_tmp_err*4, frac_tmp+frac_tmp_err*4);

            model_pdf =RooAddPdf("model_pdf"+label+"_"+self.channel+mass_spectrum,"model_pdf"+label+"_"+self.channel+mass_spectrum,RooArgList(gaus1,gaus2),RooArgList(rrv_frac),1)

        if in_model_name == "2_2Gaus":#for VV m_j

            mean1_tmp     =8.3145e+01;  mean1_tmp_err     =1.63e-01;
            deltamean_tmp =6.6321e+00;  deltamean_tmp_err =1.21e+00;
            sigma1_tmp    =7.5097e+00;  sigma1_tmp_err    =2.01e-01;
            scalesigma_tmp=3.8707e+00;  scalesigma_tmp_err=2.20e-01;
            frac_tmp      =6.4728e-01;  frac_tmp_err      =2.03e-02; 


            if self.wtagger_cut==0.43:
                mean1_tmp     =8.3089e+01;  mean1_tmp_err     =1.61e-01;
                deltamean_tmp =9.3065e+00;  deltamean_tmp_err =1.67e+00;
                sigma1_tmp    =7.5280e+00;  sigma1_tmp_err    =1.91e-01;
                scalesigma_tmp=3.4619e+00;  scalesigma_tmp_err=2.29e-01;
                frac_tmp      =7.4246e-01;  frac_tmp_err      =2.11e-02; 

            if self.wtagger_cut==0.50:
                mean1_tmp     =8.3141e+01;  mean1_tmp_err     =1.63e-01;
                deltamean_tmp =6.9129e+00;  deltamean_tmp_err =1.24e+00;
                sigma1_tmp    =7.5145e+00;  sigma1_tmp_err    =1.99e-01;
                scalesigma_tmp=3.6819e+00;  scalesigma_tmp_err=2.11e-01;
                frac_tmp      =6.7125e-01;  frac_tmp_err      =2.09e-02;

            rrv_shift = RooRealVar("rrv_shift"+label+"_"+self.channel+mass_spectrum,"rrv_shift"+label+"_"+self.channel+mass_spectrum,10.8026)   # Z mass: 91.1876;  shift=91.1876-80.385=10.8026

            rrv_mean1_gaus  = RooRealVar("rrv_mean1_gaus"+label+"_"+self.channel+mass_spectrum,"rrv_mean1_gaus"+label+"_"+self.channel+mass_spectrum,mean1_tmp, mean1_tmp-4, mean1_tmp+4);
            rrv_sigma1_gaus = RooRealVar("rrv_sigma1_gaus"+label+"_"+self.channel+mass_spectrum,"rrv_sigma1_gaus"+label+"_"+self.channel+mass_spectrum,sigma1_tmp, sigma1_tmp-4,sigma1_tmp+4 );
            gaus1 = RooGaussian("gaus1"+label+"_"+self.channel+mass_spectrum,"gaus1"+label+"_"+self.channel+mass_spectrum, rrv_x,rrv_mean1_gaus,rrv_sigma1_gaus);

            rrv_deltamean_gaus = RooRealVar("rrv_deltamean_gaus"+label+"_"+self.channel+mass_spectrum,"rrv_deltamean_gaus"+label+"_"+self.channel+mass_spectrum,deltamean_tmp, deltamean_tmp-deltamean_tmp_err*4, deltamean_tmp+deltamean_tmp_err*4); 
            rrv_deltamean_gaus = RooRealVar("rrv_deltamean_gaus"+label+"_"+self.channel+mass_spectrum,"rrv_deltamean_gaus"+label+"_"+self.channel+mass_spectrum,0.,-8,10); 
            rrv_mean2_gaus = RooFormulaVar("rrv_mean2_gaus"+label+"_"+self.channel+mass_spectrum,"@0+@1",RooArgList(rrv_mean1_gaus, rrv_deltamean_gaus));
            rrv_scalesigma_gaus = RooRealVar("rrv_scalesigma_gaus"+label+"_"+self.channel+mass_spectrum,"rrv_scalesigma_gaus"+label+"_"+self.channel+mass_spectrum,scalesigma_tmp, scalesigma_tmp-scalesigma_tmp_err*10, scalesigma_tmp+scalesigma_tmp_err*10); 
            rrv_sigma2_gaus = RooFormulaVar("rrv_sigma2_gaus"+label+"_"+self.channel+mass_spectrum,"@0*@1", RooArgList(rrv_sigma1_gaus,rrv_scalesigma_gaus));
            gaus2 = RooGaussian("gaus2"+label+"_"+self.channel+mass_spectrum,"gaus2"+label+"_"+self.channel+mass_spectrum, rrv_x,rrv_mean2_gaus,rrv_sigma2_gaus);

            rrv_frac1  = RooRealVar("rrv_frac1"+label+"_"+self.channel+mass_spectrum,"rrv_frac1"+label+"_"+self.channel+mass_spectrum,frac_tmp, frac_tmp-frac_tmp_err*4, frac_tmp+frac_tmp_err*4);

            gausguas_1 = RooAddPdf("gausguas_1"+label+"_"+self.channel+mass_spectrum+mass_spectrum,"gausguas_1"+label+"_"+self.channel+mass_spectrum+mass_spectrum,RooArgList(gaus1,gaus2),RooArgList(rrv_frac1),1)

            rrv_mean3_gaus = RooFormulaVar("rrv_mean3_gaus"+label+"_"+self.channel+mass_spectrum,"@0+@1",RooArgList(rrv_mean1_gaus, rrv_shift));
            rrv_mean4_gaus = RooFormulaVar("rrv_mean4_gaus"+label+"_"+self.channel+mass_spectrum,"@0+@1",RooArgList(rrv_mean2_gaus, rrv_shift));

            gaus3 = RooGaussian("gaus3"+label+"_"+self.channel+mass_spectrum,"gaus3"+label+"_"+self.channel+mass_spectrum, rrv_x,rrv_mean3_gaus,rrv_sigma1_gaus);
            gaus4 = RooGaussian("gaus4"+label+"_"+self.channel+mass_spectrum,"gaus4"+label+"_"+self.channel+mass_spectrum, rrv_x,rrv_mean4_gaus,rrv_sigma2_gaus);

            gausguas_2 = RooAddPdf("gausguas_2"+label+"_"+self.channel+mass_spectrum+mass_spectrum,"gausguas_2"+label+"_"+self.channel+mass_spectrum+mass_spectrum,RooArgList(gaus3,gaus4),RooArgList(rrv_frac1),1)

            rrv_frac  = RooRealVar("rrv_frac"+label+"_"+self.channel+mass_spectrum,"rrv_frac"+label+"_"+self.channel+mass_spectrum,0.74)#,0.5,1.0);
            model_pdf = RooAddPdf("model_pdf"+label+"_"+self.channel+mass_spectrum,"model_pdf"+label+"_"+self.channel+mass_spectrum,RooArgList(gausguas_1,gausguas_2),RooArgList(rrv_frac),1)


        if in_model_name == "2Gaus_ErfExp":
#            mean1_tmp     =8.3145e+01;  mean1_tmp_err     =1.63e-01;
            mean1_tmp     =8.2e+01;  mean1_tmp_err     =4;
            deltamean_tmp =6.6321e+00;  deltamean_tmp_err =1.21e+00;
#            sigma1_tmp    =7.5097e+00;  sigma1_tmp_err    =2.01e-01;
            sigma1_tmp    =7.5097e+00;  sigma1_tmp_err    =4;
            scalesigma_tmp=3.8707e+00;  scalesigma_tmp_err=2.20e-01;
            frac_tmp      =6.4728e-01;  frac_tmp_err      =2.03e-02; 

            if self.wtagger_cut==0.43:
                mean1_tmp     =8.3089e+01;  mean1_tmp_err     =1.61e-01;
                deltamean_tmp =9.3065e+00;  deltamean_tmp_err =1.67e+00;
                sigma1_tmp    =7.5280e+00;  sigma1_tmp_err    =1.91e-01;
                scalesigma_tmp=3.4619e+00;  scalesigma_tmp_err=2.29e-01;
                frac_tmp      =7.4246e-01;  frac_tmp_err      =2.11e-02; 
            if self.wtagger_cut==0.50:
                mean1_tmp     =8.3141e+01;  mean1_tmp_err     =1.63e-01;
                deltamean_tmp =6.9129e+00;  deltamean_tmp_err =1.24e+00;
                sigma1_tmp    =7.5145e+00;  sigma1_tmp_err    =1.99e-01;
                scalesigma_tmp=3.6819e+00;  scalesigma_tmp_err=2.11e-01;
                frac_tmp      =6.7125e-01;  frac_tmp_err      =2.09e-02;

            rrv_mean1_gaus  = RooRealVar("rrv_mean1_gaus"+label+"_"+self.channel+mass_spectrum,"rrv_mean1_gaus"+label+"_"+self.channel+mass_spectrum,mean1_tmp, mean1_tmp-8, mean1_tmp+8);
            rrv_sigma1_gaus = RooRealVar("rrv_sigma1_gaus"+label+"_"+self.channel+mass_spectrum,"rrv_sigma1_gaus"+label+"_"+self.channel+mass_spectrum,sigma1_tmp, sigma1_tmp-10,sigma1_tmp+10 );
            gaus1 = RooGaussian("gaus1"+label+"_"+self.channel+mass_spectrum,"gaus1"+label+"_"+self.channel+mass_spectrum, rrv_x,rrv_mean1_gaus,rrv_sigma1_gaus);

            rrv_deltamean_gaus  = RooRealVar("rrv_deltamean_gaus"+label+"_"+self.channel+mass_spectrum,"rrv_deltamean_gaus"+label+"_"+self.channel+mass_spectrum,deltamean_tmp)#, deltamean_tmp, deltamean_tmp); 
            rrv_mean2_gaus      = RooFormulaVar("rrv_mean2_gaus"+label+"_"+self.channel+mass_spectrum,"@0+@1",RooArgList(rrv_mean1_gaus, rrv_deltamean_gaus));
            rrv_scalesigma_gaus = RooRealVar("rrv_scalesigma_gaus"+label+"_"+self.channel+mass_spectrum,"rrv_scalesigma_gaus"+label+"_"+self.channel+mass_spectrum,scalesigma_tmp)#, scalesigma_tmp, scalesigma_tmp); 
            rrv_sigma2_gaus     = RooFormulaVar("rrv_sigma2_gaus"+label+"_"+self.channel+mass_spectrum,"@0*@1", RooArgList(rrv_sigma1_gaus,rrv_scalesigma_gaus));
            gaus2 = RooGaussian("gaus2"+label+"_"+self.channel+mass_spectrum,"gaus2"+label+"_"+self.channel+mass_spectrum, rrv_x,rrv_mean2_gaus,rrv_sigma2_gaus);

            rrv_frac_2gaus = RooRealVar("rrv_frac_2gaus"+label+"_"+self.channel+mass_spectrum,"rrv_frac_2gaus"+label+"_"+self.channel+mass_spectrum,frac_tmp);#, frac_tmp-frac_tmp_err*4, frac_tmp+frac_tmp_err*4);


            c0_tmp    =   -2.8628e-02 ; c0_tmp_err     = 6.08e-03;
            offset_tmp=    7.6259e+01 ; offset_tmp_err = 9.17e+00;
            width_tmp =    3.4207e+01 ; width_tmp_err  = 3.18e+00; 

            if self.wtagger_cut==0.43:
                c0_tmp    =   -3.0807e-02 ; c0_tmp_err     = 8.16e-03;
                offset_tmp=    8.2863e+01 ; offset_tmp_err = 9.66e+00;
                width_tmp =    3.1119e+01 ; width_tmp_err  = 2.80e+00; 

            if self.wtagger_cut==0.50:
                c0_tmp    =   -2.9893e-02 ; c0_tmp_err     = 6.83e-03;
                offset_tmp=    7.9350e+01 ; offset_tmp_err = 9.35e+00;
                width_tmp =    3.3083e+01 ; width_tmp_err  = 2.97e+00; 

            rrv_c_ErfExp      = RooRealVar("rrv_c_ErfExp"+label+"_"+self.channel+mass_spectrum,"rrv_c_ErfExp"+label+"_"+self.channel+mass_spectrum,c0_tmp, c0_tmp-4e-2, c0_tmp+4e-2  );
            rrv_offset_ErfExp = RooRealVar("rrv_offset_ErfExp"+label+"_"+self.channel+mass_spectrum,"rrv_offset_ErfExp"+label+"_"+self.channel+mass_spectrum, offset_tmp)#, offset_tmp-offset_tmp_err*4,offset_tmp+offset_tmp_err*4);
            #rrv_width_ErfExp = RooRealVar("rrv_width_ErfExp"+label+"_"+self.channel+mass_spectrum,"rrv_width_ErfExp"+label+"_"+self.channel+mass_spectrum, width_tmp, width_tmp-width_tmp_err*4, width_tmp+width_tmp_err*4);
            rrv_width_ErfExp  = RooRealVar("rrv_width_ErfExp"+label+"_"+self.channel+mass_spectrum,"rrv_width_ErfExp"+label+"_"+self.channel+mass_spectrum, width_tmp, width_tmp-10, width_tmp+10);
            erfexp = ROOT.RooErfExpPdf("erfexp"+label+"_"+self.channel+mass_spectrum+mass_spectrum,"erfexp"+label+"_"+self.channel+mass_spectrum+mass_spectrum,rrv_x,rrv_c_ErfExp,rrv_offset_ErfExp,rrv_width_ErfExp);

            rrv_frac  = RooRealVar("rrv_frac"+label+"_"+self.channel+mass_spectrum,"rrv_frac"+label+"_"+self.channel+mass_spectrum, 0.5,0.,1.);
            model_pdf = RooAddPdf("model_pdf"+label+"_"+self.channel+mass_spectrum,"model_pdf"+label+"_"+self.channel+mass_spectrum,RooArgList(erfexp, gaus1,gaus2),RooArgList(rrv_frac, rrv_frac_2gaus),1)

    
        if in_model_name == "ErfExpVoigGaus":
            rrv_c_ErfExp      = RooRealVar("rrv_c_ErfExp"+label+"_"+self.channel+mass_spectrum,"rrv_c_ErfExp"+label+"_"+self.channel+mass_spectrum,-0.1,-10.,0.);
            rrv_offset_ErfExp = RooRealVar("rrv_offset_ErfExp"+label+"_"+self.channel+mass_spectrum,"rrv_offset_ErfExp"+label+"_"+self.channel+mass_spectrum,100.,10.,140.);
            rrv_width_ErfExp  = RooRealVar("rrv_width_ErfExp"+label+"_"+self.channel+mass_spectrum,"rrv_width_ErfExp"+label+"_"+self.channel+mass_spectrum,30.,10,100.);

            rrv_mean_voig  = RooRealVar("rrv_mean_voig"+label+"_"+self.channel+mass_spectrum,"rrv_mean_voig"+label+"_"+self.channel+mass_spectrum,84,78,88);
            rrv_width_voig = RooRealVar("rrv_width_voig"+label+"_"+self.channel+mass_spectrum,"rrv_width_voig"+label+"_"+self.channel+mass_spectrum,7,1,20);
            rrv_sigma_voig = RooRealVar("rrv_sigma_voig"+label+"_"+self.channel+mass_spectrum,"rrv_sigma_voig"+label+"_"+self.channel+mass_spectrum,5,1,100);

            rrv_high1 = RooRealVar("rrv_high1"+label+"_"+self.channel+mass_spectrum,"rrv_high1"+label+"_"+self.channel+mass_spectrum,1,0.,200.);
            rrv_mean_gaus  = RooRealVar("rrv_mean_gaus"+label+"_"+self.channel+mass_spectrum,"rrv_mean_gaus"+label+"_"+self.channel+mass_spectrum,174)#,160,187);
            rrv_sigma_gaus = RooRealVar("rrv_sigma_gaus"+label+"_"+self.channel+mass_spectrum,"rrv_sigma_gaus"+label+"_"+self.channel+mass_spectrum,20)#,0.1,100);
            rrv_high2 = RooRealVar("rrv_high2"+label+"_"+self.channel+mass_spectrum,"rrv_high2"+label+"_"+self.channel+mass_spectrum,0.)#,0.,0.);

            model_pdf = ROOT.RooErfExp_Voig_Gaus_Pdf("model_pdf"+label+"_"+self.channel+mass_spectrum,"model_pdf"+label+"_"+self.channel+mass_spectrum, rrv_x,rrv_c_ErfExp,rrv_offset_ErfExp,rrv_width_ErfExp,rrv_mean_voig,rrv_width_voig,rrv_sigma_voig,rrv_high1,rrv_mean_gaus,rrv_sigma_gaus,rrv_high2 );

        if in_model_name == "User1":
            rrv_p0 = RooRealVar("rrv_p0_User1"+label+"_"+self.channel+mass_spectrum,"rrv_p0_User1"+label+"_"+self.channel+mass_spectrum, 6, 0,100);
            rrv_p1 = RooRealVar("rrv_p1_User1"+label+"_"+self.channel+mass_spectrum,"rrv_p1_User1"+label+"_"+self.channel+mass_spectrum, -3,-30,0);
            model_pdf = RooUser1Pdf("model_pdf"+label+"_"+self.channel+mass_spectrum,"model_pdf"+label+"_"+self.channel+mass_spectrum,rrv_x,rrv_p0,rrv_p1);

        if in_model_name == "QCD":
            rrv_p0 = RooRealVar("rrv_p0_QCD"+label+"_"+self.channel+mass_spectrum,"rrv_p0_QCD"+label+"_"+self.channel+mass_spectrum,  0,-200,200);
            rrv_p1 = RooRealVar("rrv_p1_QCD"+label+"_"+self.channel+mass_spectrum,"rrv_p1_QCD"+label+"_"+self.channel+mass_spectrum,  0,-200,200);
            rrv_p2 = RooRealVar("rrv_p2_QCD"+label+"_"+self.channel+mass_spectrum,"rrv_p2_QCD"+label+"_"+self.channel+mass_spectrum,  0,-200,200);
            model_pdf = RooQCDPdf("model_pdf"+label+"_"+self.channel+mass_spectrum,"model_pdf"+label+"_"+self.channel+mass_spectrum,rrv_x,rrv_p0,rrv_p1,rrv_p2);

        if in_model_name == "QCD_v2":#can replace exp 
            rrv_p0 = RooRealVar("rrv_p0_QCD"+label+"_"+self.channel+mass_spectrum,"rrv_p0_QCD"+label+"_"+self.channel+mass_spectrum, -15,-50,0);
            rrv_p1 = RooRealVar("rrv_p1_QCD"+label+"_"+self.channel+mass_spectrum,"rrv_p1_QCD"+label+"_"+self.channel+mass_spectrum,  20,0,250);
            rrv_p2 = RooRealVar("rrv_p2_QCD"+label+"_"+self.channel+mass_spectrum,"rrv_p2_QCD"+label+"_"+self.channel+mass_spectrum,0,-20,20);
            model_pdf = RooQCDPdf("model_pdf"+label+"_"+self.channel+mass_spectrum,"model_pdf"+label+"_"+self.channel+mass_spectrum,rrv_x,rrv_p0,rrv_p1,rrv_p2);

        if in_model_name == "Pow" or in_model_name == "Pow_sr" :#can replace exp
            rrv_c = RooRealVar("rrv_c_Pow"+label+"_"+self.channel+mass_spectrum,"rrv_c_Pow"+label+"_"+self.channel+mass_spectrum, -5, -20, 0);
            model_pdf = RooPowPdf("model_pdf"+label+"_"+self.channel+mass_spectrum,"model_pdf"+label+"_"+self.channel+mass_spectrum,rrv_x, rrv_c );
 
        if in_model_name == "Pow2":
            rrv_c0 = RooRealVar("rrv_c0_Pow2"+label+"_"+self.channel+mass_spectrum,"rrv_c0_Pow2"+label+"_"+self.channel+mass_spectrum, 5, 0, 20);
            rrv_c1 = RooRealVar("rrv_c1_Pow2"+label+"_"+self.channel+mass_spectrum,"rrv_c1_Pow2"+label+"_"+self.channel+mass_spectrum, 0, -5 , 5);
            model_pdf = RooPow2Pdf("model_pdf"+label+"_"+self.channel+mass_spectrum,"model_pdf"+label+"_"+self.channel+mass_spectrum, rrv_x, rrv_c0, rrv_c1 );

        if in_model_name == "ErfPow_v1":#can replace erf*exp 
            rrv_c = RooRealVar("rrv_c_ErfPow"+label+"_"+self.channel+mass_spectrum,"rrv_c_ErfPow"+label+"_"+self.channel+mass_spectrum, -5,-10,0);
            rrv_offset = RooRealVar("rrv_offset_ErfPow"+label+"_"+self.channel+mass_spectrum,"rrv_offset_ErfPow"+label+"_"+self.channel+mass_spectrum, 450,350,550);
            rrv_width  = RooRealVar("rrv_width_ErfPow"+label+"_"+self.channel+mass_spectrum,"rrv_width_ErfPow"+label+"_"+self.channel+mass_spectrum,50,20,90);
            model_pdf  = RooErfPowPdf("model_pdf"+label+"_"+self.channel+mass_spectrum,"model_pdf"+label+"_"+self.channel+mass_spectrum,rrv_x,rrv_c,rrv_offset,rrv_width);

        if in_model_name == "ErfPow_v1_M":#can replace erf*exp 
            rrv_c = RooRealVar("rrv_c_ErfPow"+label+"_"+self.channel+mass_spectrum,"rrv_c_ErfPow"+label+"_"+self.channel+mass_spectrum, -5,-10,0);
            rrv_offset = RooRealVar("rrv_offset_ErfPow"+label+"_"+self.channel+mass_spectrum,"rrv_offset_ErfPow"+label+"_"+self.channel+mass_spectrum, 450,350,600);
            rrv_width  = RooRealVar("rrv_width_ErfPow"+label+"_"+self.channel+mass_spectrum,"rrv_width_ErfPow"+label+"_"+self.channel+mass_spectrum,30,0,90);
            model_pdf  = RooErfPowPdf("model_pdf"+label+"_"+self.channel+mass_spectrum,"model_pdf"+label+"_"+self.channel+mass_spectrum,rrv_x,rrv_c,rrv_offset,rrv_width);            

        if in_model_name == "ErfPow2_v1":#can replace erf*exp 
            rrv_c0 = RooRealVar("rrv_c0_ErfPow2"+label+"_"+self.channel+mass_spectrum,"rrv_c0_ErfPow2"+label+"_"+self.channel+mass_spectrum,14,1,30);
            rrv_c1 = RooRealVar("rrv_c1_ErfPow2"+label+"_"+self.channel+mass_spectrum,"rrv_c1_ErfPow2"+label+"_"+self.channel+mass_spectrum, 5,-5,10);
            rrv_offset = RooRealVar("rrv_offset_ErfPow2"+label+"_"+self.channel+mass_spectrum,"rrv_offset_ErfPow2"+label+"_"+self.channel+mass_spectrum, 600,400,900);
            rrv_width  = RooRealVar("rrv_width_ErfPow2"+label+"_"+self.channel+mass_spectrum,"rrv_width_ErfPow2"+label+"_"+self.channel+mass_spectrum,80,10,350);
            model_pdf  = RooErfPow2Pdf("model_pdf"+label+"_"+self.channel+mass_spectrum,"model_pdf"+label+"_"+self.channel+mass_spectrum,rrv_x,rrv_c0,rrv_c1,rrv_offset,rrv_width);

        if in_model_name == "ErfPow2_v1_sr":#can replace erf*exp 
            rrv_c0 = RooRealVar("rrv_c0_ErfPow2"+label+"_"+self.channel+mass_spectrum,"rrv_c0_ErfPow2"+label+"_"+self.channel+mass_spectrum, 4,2, 8);
            rrv_c1 = RooRealVar("rrv_c1_ErfPow2"+label+"_"+self.channel+mass_spectrum,"rrv_c1_ErfPow2"+label+"_"+self.channel+mass_spectrum, -0.5,-2,0);
            rrv_offset = RooRealVar("rrv_offset_ErfPow2"+label+"_"+self.channel+mass_spectrum,"rrv_offset_ErfPow2"+label+"_"+self.channel+mass_spectrum, 490,440,520);
            rrv_width = RooRealVar("rrv_width_ErfPow2"+label+"_"+self.channel+mass_spectrum,"rrv_width_ErfPow2"+label+"_"+self.channel+mass_spectrum,50,30,80);
            model_pdf = RooErfPow2Pdf("model_pdf"+label+"_"+self.channel+mass_spectrum,"model_pdf"+label+"_"+self.channel+mass_spectrum,rrv_x,rrv_c0,rrv_c1,rrv_offset,rrv_width);


        if in_model_name == "ErfPowExp_v1":#can replace erf*exp 
            rrv_c0 = RooRealVar("rrv_c0_ErfPowExp"+label+"_"+self.channel+mass_spectrum,"rrv_c0_ErfPowExp"+label+"_"+self.channel+mass_spectrum,13,5,40);
            rrv_c1 = RooRealVar("rrv_c1_ErfPowExp"+label+"_"+self.channel+mass_spectrum,"rrv_c1_ErfPowExp"+label+"_"+self.channel+mass_spectrum, 2,0,4);
            rrv_offset = RooRealVar("rrv_offset_ErfPowExp"+label+"_"+self.channel+mass_spectrum,"rrv_offset_ErfPowExp"+label+"_"+self.channel+mass_spectrum, 450,400,600);
            rrv_width  = RooRealVar("rrv_width_ErfPowExp"+label+"_"+self.channel+mass_spectrum,"rrv_width_ErfPowExp"+label+"_"+self.channel+mass_spectrum,30,15,150);
            model_pdf  = RooErfPowExpPdf("model_pdf"+label+"_"+self.channel+mass_spectrum,"model_pdf"+label+"_"+self.channel+mass_spectrum,rrv_x,rrv_c0,rrv_c1,rrv_offset,rrv_width);

        if in_model_name == "ErfPowExp_v1_sr":#can replace erf*exp 
            rrv_c0 = RooRealVar("rrv_c0_ErfPowExp"+label+"_"+self.channel+mass_spectrum,"rrv_c0_ErfPowExp"+label+"_"+self.channel+mass_spectrum,6,2,15);
            rrv_c1 = RooRealVar("rrv_c1_ErfPowExp"+label+"_"+self.channel+mass_spectrum,"rrv_c1_ErfPowExp"+label+"_"+self.channel+mass_spectrum, -1,-3,2);
            rrv_offset = RooRealVar("rrv_offset_ErfPowExp"+label+"_"+self.channel+mass_spectrum,"rrv_offset_ErfPowExp"+label+"_"+self.channel+mass_spectrum, 490,440,520);
            rrv_width  = RooRealVar("rrv_width_ErfPowExp"+label+"_"+self.channel+mass_spectrum,"rrv_width_ErfPowExp"+label+"_"+self.channel+mass_spectrum,50,30,70);
            model_pdf  = RooErfPowExpPdf("model_pdf"+label+"_"+self.channel+mass_spectrum,"model_pdf"+label+"_"+self.channel+mass_spectrum,rrv_x,rrv_c0,rrv_c1,rrv_offset,rrv_width);

        if in_model_name == "ErfPowExp_v1_0":#difference inital value
            rrv_c0 = RooRealVar("rrv_c0_ErfPowExp"+label+"_"+self.channel+mass_spectrum,"rrv_c0_ErfPowExp"+label+"_"+self.channel+mass_spectrum,20,15,40);
            rrv_c1 = RooRealVar("rrv_c1_ErfPowExp"+label+"_"+self.channel+mass_spectrum,"rrv_c1_ErfPowExp"+label+"_"+self.channel+mass_spectrum, 1.6,0.5,5);
            rrv_offset = RooRealVar("rrv_offset_ErfPowExp"+label+"_"+self.channel+mass_spectrum,"rrv_offset_ErfPowExp"+label+"_"+self.channel+mass_spectrum, 470,420,520);
            rrv_width  = RooRealVar("rrv_width_ErfPowExp"+label+"_"+self.channel+mass_spectrum,"rrv_width_ErfPowExp"+label+"_"+self.channel+mass_spectrum,47,30,60);
            model_pdf  = RooErfPowExpPdf("model_pdf"+label+"_"+self.channel+mass_spectrum,"model_pdf"+label+"_"+self.channel+mass_spectrum,rrv_x,rrv_c0,rrv_c1,rrv_offset,rrv_width);

        if in_model_name == "Keys":
            rdataset  = self.workspace4fit_.data("rdataset_%s_signal_region_mlvj"%(self.higgs_sample))
            model_pdf = RooKeysPdf("model_pdf"+label+"_"+self.channel+mass_spectrum+mass_spectrum,"model_pdf"+label+"_"+self.channel+mass_spectrum+mass_spectrum, rrv_x,rdataset);

        getattr(self.workspace4fit_,"import")(model_pdf)
        return self.workspace4fit_.pdf("model_pdf"+label+"_"+self.channel+mass_spectrum)

    ########### Gaussian contraint of a parameter of a pdf
    def addConstraint(self, rrv_x, x_mean, x_sigma, ConstraintsList):
     print "########### Add to Contraint List some parameters  ############"
     rrv_x_mean = RooRealVar(rrv_x.GetName()+"_mean",rrv_x.GetName()+"_mean",x_mean );
     rrv_x_sigma = RooRealVar(rrv_x.GetName()+"_sigma",rrv_x.GetName()+"_sigma",x_sigma );
     constrainpdf_x = RooGaussian("constrainpdf_"+rrv_x.GetName(),"constrainpdf_"+rrv_x.GetName(),rrv_x, rrv_x_mean, rrv_x_sigma);
     ## import in the workspace and save the name of constriant pdf
     getattr(self.workspace4fit_,"import")(constrainpdf_x)
     ConstraintsList.append(constrainpdf_x.GetName());

    ### get an mj model from the workspace givin the label
    def get_mj_Model(self,label, relaxed = 0):
       if relaxed == 0:  
        return self.workspace4fit_.pdf("model"+label+"_"+self.channel+"_mj")
       else:
        return self.workspace4fit_.pdf("model"+label+"_"+self.channel+"_mj_relaxed")

    ### take the dataset, the model , the parameters in order to fix them as constant --> for extended pdf
    def get_General_mj_Model(self, label, relaxed = 0 ):
        print "########### Fixing a general mj model  ############"
        if relaxed == 0:
         rdataset_General_mj = self.workspace4fit_.data("rdataset%s_%s_mj"%(label,self.channel))
        else:
         rdataset_General_mj = self.workspace4fit_.data("rdataset%s_%s_mj_relaxed"%(label,self.channel))            
        model_General = self.get_mj_Model(label, relaxed);
        rdataset_General_mj.Print();
        model_General.Print();
        ## get the parameters and cycle on them
        parameters_General = model_General.getParameters(rdataset_General_mj);
        par=parameters_General.createIterator();
        par.Reset();
        param=par.Next()
        while (param):
            if (TString(label).Contains("VV") or TString(label).Contains("VV") or TString(label).Contains("STop") or TString(label).Contains("TTbar")):
                param.Print();
            param.setConstant(kTRUE);
            param=par.Next()
        ## return the pdf after having fixed the paramters
        return model_General ;

    ### fix only the ttbar component using the default label --> for extended pdf
    def get_TTbar_mj_Model(self,label="_TTbar", relaxed = 0):
        print "########### Fixing only the TTbar mj Shape  ############"
        return self.get_General_mj_Model(label,relaxed);

    ### fix only the stop component using the default label --> for extended pdf
    def get_STop_mj_Model(self,label="_STop", relaxed = 0):
        print "########### Fixing only the Stop mj Shape  ############"
        return self.get_General_mj_Model(label,relaxed);

    ### fix only the VV component using the default label --> for extended pdf
    def get_VV_mj_Model(self,label="_VV",relaxed = 0):
        print "########### Fixing only the VV mj Shape  ############"
        return self.get_General_mj_Model(label,relaxed);

    ### fix only the WW_EWK component using the default label --> for extended pdf
    def get_WW_EWK_mj_Model(self,label="_WW_EWK",relaxed = 0):
        print "########### Fixing only the WW_EWK mj Shape  ############"
        return self.get_General_mj_Model(label,relaxed);
    

    ### fix only the WJets model --> for extended pdf (just fix shape parameters of width, offset of ErfExp and p1 of User1 function
    def get_WJets_mj_Model(self,label, relaxed = 0):
        print "########### Fixing only the WJets mj Shape --> just the printed parameters  ############"
        if relaxed == 0:
         rdataset_WJets_mj = self.workspace4fit_.data("rdataset%s_%s_mj"%(label,self.channel))
        else:
         rdataset_WJets_mj = self.workspace4fit_.data("rdataset%s_%s_mj_relaxed"%(label,self.channel)) 

        model_WJets = self.get_mj_Model(label, relaxed);
        rdataset_WJets_mj.Print();
        model_WJets.Print();
        return self.get_mj_Model(label,relaxed);

    ### fix a given model taking the label, and the region --> for extended pdf --> all the parameter of the pdf + normalization
    def fix_Model(self, label, mlvj_region="_signal_region",mass_spectrum="_mlvj", relaxed=0):
        print "########### Fixing an Extended Pdf for mlvj  ############"

        if relaxed==0:
          rdataset = self.workspace4fit_.data("rdataset%s%s_%s%s"%(label,mlvj_region,self.channel,mass_spectrum))
        else:
          rdataset = self.workspace4fit_.data("rdataset%s%s_%s%s_relaxed"%(label,mlvj_region,self.channel,mass_spectrum))

        model = self.get_mlvj_Model(label,mlvj_region, relaxed);
        rdataset.Print();
        model.Print();
        parameters = model.getParameters(rdataset);
        par=parameters.createIterator(); par.Reset();
        param=par.Next()
        while (param):
            param.setConstant(kTRUE);
            param=par.Next()

    ### fix a pdf in a different way --> for RooAbsPdf
    def fix_Pdf(self,model_pdf,argset_notparameter):
        print "########### Fixing a RooAbsPdf for mlvj or mj  ############"
        parameters = model_pdf.getParameters(argset_notparameter);
        par=parameters.createIterator(); par.Reset();
        param=par.Next()
        while (param):
            param.setConstant(kTRUE);
            param.Print();
            param=par.Next()

    ### print the parameters of a given pdf --> only non constant ones
    def ShowParam_Pdf(self,model_pdf,argset_notparameter):
        print "########### Show Parameters of a input model  ############"
        model_pdf.Print()
        parameters = model_pdf.getParameters(argset_notparameter);
        par = parameters.createIterator(); par.Reset();
        param = par.Next()
        while (param):
            if not param.isConstant():
                param.Print();
                if (param.getVal()-param.getMin())< param.getError()*1 or (param.getMax()- param.getVal())< param.getError()*1:
                    param.Print();
            param=par.Next()


    #### get a generic mlvj model from the workspace
    def get_mlvj_Model(self,label, mlvj_region, relaxed=0):
      if relaxed==0:
        return self.workspace4fit_.pdf("model"+label+mlvj_region+"_"+self.channel+"_mlvj");
      else:
        return self.workspace4fit_.pdf("model"+label+mlvj_region+"_"+self.channel+"_mlvj_relaxed");

    #### get a general mlvj model and fiz the paramters --> for extended pdf
    def get_General_mlvj_Model(self, label, mlvj_region="_signal_region", relaxed=0):
        print "########### Fixing a general mlvj model  ############"
        if relaxed==0: rdataset_General_mlvj = self.workspace4fit_.data("rdataset%s%s_%s_mlvj"%(label, mlvj_region,self.channel))
        else: rdataset_General_mlvj = self.workspace4fit_.data("rdataset%s%s_%s_mlvj_relaxed"%(label, mlvj_region,self.channel))          
        model_General = self.get_mlvj_Model(label,mlvj_region,relaxed);
        rdataset_General_mlvj.Print();
        model_General.Print();
        parameters_General = model_General.getParameters(rdataset_General_mlvj);
        par=parameters_General.createIterator(); par.Reset();
        param=par.Next()
        while (param):
            param.setConstant(kTRUE);
            param.Print();
            param=par.Next()
        return self.get_mlvj_Model(label,mlvj_region,relaxed);

    ###### get TTbar model mlvj in a region
    def get_TTbar_mlvj_Model(self, mlvj_region="_signal_region", relaxed=0):
        print "########### Fixing TTbar mlvj model for the region",mlvj_region,"  ############"
        return self.get_General_mlvj_Model("_TTbar",mlvj_region,relaxed);

    ###### get Single Top model mlvj in a region
    def get_STop_mlvj_Model(self, mlvj_region="_signal_region", relaxed=0):
        print "########### Fixing Stop mlvj model for the region",mlvj_region,"  ############"
        return self.get_General_mlvj_Model("_STop",mlvj_region,relaxed);

    ###### get VV mlvj in a region
    def get_VV_mlvj_Model(self, mlvj_region="_signal_region", relaxed=0):
        print "########### Fixing VV mlvj for the region",mlvj_region,"  ############"
        return self.get_General_mlvj_Model("_VV",mlvj_region,relaxed);

    ###### get WW_EWK mlvj in a region
    def get_WW_EWK_mlvj_Model(self, mlvj_region="_signal_region", relaxed=0):
        print "########### Fixing WW_EWK mlvj for the region",mlvj_region,"  ############"
        return self.get_General_mlvj_Model("_WW_EWK",mlvj_region,relaxed);    

    ###### get ggH mlvj in a region
    def get_ggH_mlvj_Model(self, mlvj_region="_signal_region"):
        print "########### Fixing ggH mlvj for the region",mlvj_region,"  ############"                 
        return self.get_General_mlvj_Model("_%s"%(self.higgs_sample),mlvj_region);

    ###### get vbfH mlvj in a region
    def get_vbfH_mlvj_Model(self, mlvj_region="_signal_region"):
        print "########### Fixing vbfH mlvj for the region",mlvj_region,"  ############"                 
        return self.get_General_mlvj_Model("_%s"%(self.vbfhiggs_sample),mlvj_region);

    ###### get W+jets mlvj in a region
    def get_WJets_mlvj_Model(self, mlvj_region="_signal_region"):
        rdataset_WJets_mlvj = self.workspace4fit_.data("rdataset_WJets_%s_mlvj"%(mlvj_region))
	model_WJets = self.get_mlvj_Model("_WJets0",mlvj_region);
	print "######## get Wjet mlvj model for the region --> set constant just the normalization from mj fit",mlvj_region," ########";
        rdataset_WJets_mlvj.Print()
        model_WJets.Print()
        parameters_WJets = model_WJets.getParameters(rdataset_WJets_mlvj);
        par = parameters_WJets.createIterator();
        par.Reset();
        param=par.Next()
        while (param):
            paraName=TString(param.GetName());
            param.Print();
            if paraName.Contains("rrv_number_WJets"): ## set the correct normalization for W+jets if we are inside the signal region and fix it as constant
                if self.workspace4fit_.var("rrv_number_WJets_in_mj%s_from_fitting_%s"%(mlvj_region,self.channel)):
                    self.workspace4fit_.var("rrv_number_WJets_in_mj%s_from_fitting_%s"%(mlvj_region,self.channel)).Print()
                    param.setVal( self.workspace4fit_.var("rrv_number_WJets_in_mj%s_from_fitting_%s"%(mlvj_region,self.channel)).getVal() )
                if mlvj_region=="_signal_region": param.setConstant(kTRUE);
            param.Print();
            param=par.Next()
        return self.get_mlvj_Model("_WJets0_xww",mlvj_region);

    ### change a dataset to a histpdf roofit object
    def change_dataset_to_histpdf(self,x,dataset):
        print "######## change the dataset into a histpdf  ########"
        datahist = dataset.binnedClone(dataset.GetName()+"_binnedClone",dataset.GetName()+"_binnedClone")
        histpdf = RooHistPdf(dataset.GetName()+"_histpdf",dataset.GetName()+"_histpdf",RooArgSet(x),datahist)
        dataset.Print();
        histpdf.Print();
        getattr(self.workspace4fit_,"import")(histpdf)

    ### change from a dataset to a histogramm of Roofit
    def change_dataset_to_histogram(self, x,dataset,label=""):
        print "######## change the dataset into a histogramm for mj distribution ########"
        datahist=dataset.binnedClone(dataset.GetName()+"_binnedClone",dataset.GetName()+"_binnedClone")
        nbin=int( (x.getMax()-x.getMin())/self.BinWidth_mj);
        if label=="":
            return datahist.createHistogram("histo_%s"%(dataset.GetName()),x, RooFit.Binning( nbin ,x.getMin(),x.getMax()));
        else:
            return datahist.createHistogram("histo_"+label,x, RooFit.Binning( nbin,x.getMin(),x.getMax()));
        

    ### Define the Extended Pdf for and mJ fit giving: label, fit model name, list constraint and ismc
    def make_Model(self, label, in_model_name, mass_spectrum="_mj", ConstraintsList=[], ismc_wjet=0, area_init_value=500):

      ##### define an extended pdf from a standard Roofit One
      print " "
      print "###############################################"
      print "## Make model : ",label," ",in_model_name,"##";
      print "###############################################"
      print " "

      rrv_number = RooRealVar("rrv_number"+label+"_"+self.channel+mass_spectrum,"rrv_number"+label+"_"+self.channel+mass_spectrum,area_init_value,0.,1e7);
      ## call the make RooAbsPdf method
      model_pdf = self.make_Pdf(label,in_model_name,mass_spectrum,ConstraintsList,ismc_wjet)
      print "######## Model Pdf ########"
      model_pdf.Print();
      
      
      ## create the extended pdf
      model = RooExtendPdf("model"+label+"_"+self.channel+mass_spectrum,"model"+label+"_"+self.channel+mass_spectrum, model_pdf, rrv_number );
      print "######## Model Extended Pdf ########"
      model.Print();

      #### put all the parameters ant the shape in the workspace
      getattr(self.workspace4fit_,"import")(rrv_number)
      getattr(self.workspace4fit_,"import")(model)
      self.workspace4fit_.pdf("model"+label+"_"+self.channel+mass_spectrum).Print();
      ## return the total extended pdf
      return self.workspace4fit_.pdf("model"+label+"_"+self.channel+mass_spectrum);

    ### Method for a single MC fit of the mj spectra giving: file name, label, model name
    def fit_mj_single_MC(self,in_file_name, label, in_model_name, additioninformation=""):

        print "############### Fit mj single MC sample",in_file_name," ",label,"  ",in_model_name," ##################"
        ## import variable and dataset
        rrv_mass_j = self.workspace4fit_.var("rrv_mass_j");
        rdataset_mj = self.workspace4fit_.data("rdataset4fit"+label+"_"+self.channel+"_mj");
        rdataset_mj_relaxed = self.workspace4fit_.data("rdataset4fit"+label+"_"+self.channel+"_mj_relaxed");
        rdataset_mj.Print();
        if(rdataset_mj_relaxed) : rdataset_mj_relaxed.Print();
        
        ## make the extended model
        model = self.make_Model(label,in_model_name);
        rfresult = model.fitTo(rdataset_mj,RooFit.Save(1), RooFit.Extended(kTRUE),   RooFit.SumW2Error(kTRUE));
        rfresult = model.fitTo(rdataset_mj,RooFit.Save(1), RooFit.SumW2Error(kTRUE) ,RooFit.Extended(kTRUE), RooFit.Minimizer("Minuit2") );
        rfresult = model.fitTo(rdataset_mj,RooFit.Save(1), RooFit.SumW2Error(kTRUE) ,RooFit.Extended(kTRUE), RooFit.Minimizer("Minuit2") );
        rfresult.Print();


        ## Plot the result
        mplot = rrv_mass_j.frame(RooFit.Title(label+" fitted by "+in_model_name), RooFit.Bins(int(rrv_mass_j.getBins()/self.narrow_factor)) );
        rdataset_mj.plotOn( mplot, RooFit.MarkerSize(1.5), RooFit.DataError(RooAbsData.SumW2), RooFit.XErrorSize(0) );

	## draw the error band for an extend pdf
        draw_error_band_extendPdf(rdataset_mj, model, rfresult,mplot,2,"L");
        ## re-draw the dataset
        rdataset_mj.plotOn( mplot , RooFit.MarkerSize(1.5), RooFit.DataError(RooAbsData.SumW2), RooFit.XErrorSize(0) );
        ## draw the function
        model.plotOn( mplot );# remove RooFit.VLines() in order to get right pull in the 1st bin

        ## Get the pull
        mplot_pull = self.get_pull(rrv_mass_j, mplot);
        mplot.GetYaxis().SetRangeUser(1e-5,mplot.GetMaximum()*1.2);

        ## CALCULATE CHI2
        datahist = rdataset_mj.binnedClone(rdataset_mj.GetName()+"_binnedClone",rdataset_mj.GetName()+"_binnedClone")
        Nbin = int(rrv_mass_j.getBins()); 
        rresult_param = rfresult.floatParsFinal();        
        nparameters =  rresult_param.getSize()                                         
        ChiSquare = model.createChi2(datahist,RooFit.Extended(kTRUE),RooFit.DataError(RooAbsData.Poisson));
        chi_over_ndf= ChiSquare.getVal()/(Nbin - nparameters);

        ## Add Chisquare to mplot_pull
        cs = TLatex(0.75,0.8,"#chi^{2}/ndf = %0.2f "%(float(chi_over_ndf)));
        cs.SetNDC();
        cs.SetTextSize(0.12);
        cs.AppendPad("same");
        mplot_pull.addObject(cs)

        parameters_list = model.getParameters(rdataset_mj);
        self.draw_canvas_with_pull( mplot, mplot_pull,parameters_list,"plots_%s_%s_%s_%s_g1/m_j_fitting%s_wtaggercut%s/"%(options.additioninformation, self.channel,self.PS_model, self.wtagger_label, additioninformation, self.wtagger_label), label+in_file_name, in_model_name)


        if label == "_STop" or label == "_VV" or label == "_WJets0" or label == "_WW_EWK" or label == "_TTbar" :

           mplot_sys = rrv_mass_j.frame( RooFit.Bins(int(rrv_mass_j.getBins()/self.narrow_factor)));
           rdataset_mj.plotOn(mplot_sys, RooFit.Name("MC Events"), RooFit.MarkerSize(1.5), RooFit.DataError(RooAbsData.SumW2), RooFit.XErrorSize(0) );
           model.plotOn(mplot_sys,RooFit.Name("Nominal MC"),RooFit.LineColor(kBlack));
           draw_error_band_extendPdf(rdataset_mj, model, rfresult,mplot_sys,self.color_palet["Uncertainty"],"F");

           if self.workspace4fit_.pdf("model%smassvbf_jes_up_%s_mj"%(label,self.channel)) :
              self.workspace4fit_.pdf("model%smassvbf_jes_up_%s_mj"%(label,self.channel)).plotOn(mplot_sys,RooFit.Name("jes_up"), RooFit.LineColor(kRed),RooFit.Normalization(self.workspace4fit_.var("rrv_number"+label+"massvbf_jes_up_"+self.channel+"_mj").getVal()/(rdataset_mj.sumEntries()*self.workspace4fit_.var("rrv_scale_to_lumi"+label+"_"+self.channel).getVal())));
           if self.workspace4fit_.pdf("model%smassvbf_jes_dn_%s_mj"%(label,self.channel)) :
              self.workspace4fit_.pdf("model%smassvbf_jes_dn_%s_mj"%(label,self.channel)).plotOn(mplot_sys,RooFit.Name("jes_dn"), RooFit.LineColor(kBlue),RooFit.Normalization(self.workspace4fit_.var("rrv_number"+label+"massvbf_jes_dn_"+self.channel+"_mj").getVal()/(rdataset_mj.sumEntries()*self.workspace4fit_.var("rrv_scale_to_lumi"+label+"_"+self.channel).getVal())));

           if self.workspace4fit_.pdf("model%smassvbf_jer_%s_mj"%(label,self.channel)) :
              self.workspace4fit_.pdf("model%smassvbf_jer_%s_mj"%(label,self.channel)).plotOn(mplot_sys,RooFit.Name("jer"), RooFit.LineColor(kAzure+1),RooFit.Normalization(self.workspace4fit_.var("rrv_number"+label+"massvbf_jer_"+self.channel+"_mj").getVal()/(rdataset_mj.sumEntries()*self.workspace4fit_.var("rrv_scale_to_lumi"+label+"_"+self.channel).getVal() )));

           if self.workspace4fit_.pdf("model%smassvbf_jer_up_%s_mj"%(label,self.channel)) :
              self.workspace4fit_.pdf("model%smassvbf_jer_up_%s_mj"%(label,self.channel)).plotOn(mplot_sys,RooFit.Name("jer_up"), RooFit.LineColor(kGreen+1),RooFit.Normalization(self.workspace4fit_.var("rrv_number"+label+"massvbf_jer_up_"+self.channel+"_mj").getVal()/(rdataset_mj.sumEntries()*self.workspace4fit_.var("rrv_scale_to_lumi"+label+"_"+self.channel).getVal())));

           if self.workspace4fit_.pdf("model%smassvbf_jer_dn_%s_mj"%(label,self.channel)) :
              self.workspace4fit_.pdf("model%smassvbf_jer_up_%s_mj"%(label,self.channel)).plotOn(mplot_sys,RooFit.Name("jer_dn"), RooFit.LineColor(6),RooFit.Normalization(self.workspace4fit_.var("rrv_number"+label+"massvbf_jer_dn_"+self.channel+"_mj").getVal()/(rdataset_mj.sumEntries()*self.workspace4fit_.var("rrv_scale_to_lumi"+label+"_"+self.channel).getVal())));

           if label == "_WJets0" and self.workspace4fit_.pdf("model_WJets01_%s_mj"%(self.channel)):
              self.workspace4fit_.pdf("model_WJets01_%s_mj"%(self.channel)).plotOn(mplot_sys,RooFit.Name("alt shape"), RooFit.LineColor(kOrange+1),RooFit.Normalization(self.workspace4fit_.var("rrv_number_WJets01_"+self.channel+"_mj").getVal()/(rdataset_mj.sumEntries()*self.workspace4fit_.var("rrv_scale_to_lumi"+label+"_"+self.channel).getVal())));
                
               
           self.leg = self.legend4Plot(mplot_sys,0,1,0., 0.06, 0.16, 0.);
           mplot_sys.addObject(self.leg);
           rdataset_mj.plotOn(mplot_sys, RooFit.Name("MC Events"), RooFit.MarkerSize(1.5), RooFit.DataError(RooAbsData.SumW2), RooFit.XErrorSize(0) );
           model.plotOn(mplot_sys,RooFit.Name("Nominal MC"),RooFit.LineColor(kBlack));
           mplot_sys.GetYaxis().SetRangeUser(1e-2,mplot_sys.GetMaximum()*1.2);

           self.draw_canvas_with_pull( mplot_sys, mplot_pull,parameters_list,"plots_%s_%s_%s_%s_g1/other/"%(options.additioninformation,self.channel,self.PS_model,self.wtagger_label),in_file_name,"m_j_extended"+label,in_model_name);
#            self.draw_canvas(mplot_sys,"plots_%s_%s_%s_%s_g1/other/"%(options.additioninformation, self.channel,self.PS_model,self.wtagger_label),in_file_name,"m_j_extended"+label,0,1);

           print "################### Decorrelated mj single mc shape ################"
           ## temp workspace for the pdf diagonalizer
           model_pdf = self.workspace4fit_.pdf("model_pdf%s_%s_mj"%(label,self.channel)); ## take the pdf from the workspace
           model_pdf.fitTo(rdataset_mj, RooFit.Save(1), RooFit.SumW2Error(kTRUE) );
           rfresult_pdf = model_pdf.fitTo( rdataset_mj, RooFit.Save(1), RooFit.SumW2Error(kTRUE), RooFit.Minimizer("Minuit2"));
           wsfit_tmp = RooWorkspace("wsfit_tmp"+label+"_"+self.channel+"_mj");
           Deco      = PdfDiagonalizer("Deco"+label+"_"+self.channel+"_"+self.wtagger_label+"_mj",wsfit_tmp,rfresult_pdf); ## in order to have a good name
           print "##################### diagonalize ";
           model_deco = Deco.diagonalize(model_pdf); ## diagonalize
           print "##################### original  parameters ";
           model_pdf.getParameters(rdataset_mj).Print("v");
           print "##################### original  decorrelated parameters ";
           model_deco.getParameters(rdataset_mj).Print("v");
           print "##################### original  pdf ";
           model_pdf.Print();
           print "##################### decorrelated pdf ";
           model_deco.Print();

           mplot_sys = rrv_mass_j.frame( RooFit.Bins(int(rrv_mass_j.getBins()/self.narrow_factor)));
           rdataset_mj.plotOn(mplot_sys, RooFit.Name("MC Events"), RooFit.MarkerSize(1.5), RooFit.DataError(RooAbsData.SumW2), RooFit.XErrorSize(0) );
           model_deco.plotOn(mplot_sys,RooFit.Name("Nominal MC"),RooFit.LineColor(kBlack));
           rrv_number_dataset = RooRealVar("rrv_number_dataset","rrv_number_dataset",rdataset_mj.sumEntries());
           rrv_number_dataset.setError(0.); ## only shape uncertainty
           draw_error_band(rdataset_mj, model_pdf,rrv_number_dataset,rfresult_pdf,mplot_sys,self.color_palet["Uncertainty"],"F"); ## draw the error band with the area

           if self.workspace4fit_.pdf("model%smassvbf_jes_up_%s_mj"%(label,self.channel)) :
              self.workspace4fit_.pdf("model%smassvbf_jes_up_%s_mj"%(label,self.channel)).plotOn(mplot_sys,RooFit.Name("jes_up"), RooFit.LineColor(kRed));

           if self.workspace4fit_.pdf("model%smassvbf_jes_dn_%s_mj"%(label,self.channel)) :
              self.workspace4fit_.pdf("model%smassvbf_jes_dn_%s_mj"%(label,self.channel)).plotOn(mplot_sys,RooFit.Name("jes_dn"), RooFit.LineColor(kBlue));

           if self.workspace4fit_.pdf("model%smassvbf_jer_%s_mj"%(label,self.channel)) :
              self.workspace4fit_.pdf("model%smassvbf_jer_%s_mj"%(label,self.channel)).plotOn(mplot_sys,RooFit.Name("jer"), RooFit.LineColor(kAzure+1));

           if self.workspace4fit_.pdf("model%smassvbf_jer_up_%s_mj"%(label,self.channel)) :
              self.workspace4fit_.pdf("model%smassvbf_jer_up_%s_mj"%(label,self.channel)).plotOn(mplot_sys,RooFit.Name("jer_up"), RooFit.LineColor(kGreen+1));

           if self.workspace4fit_.pdf("model%smassvbf_jer_dn_%s_mj"%(label,self.channel)) :
              self.workspace4fit_.pdf("model%smassvbf_jer_up_%s_mj"%(label,self.channel)).plotOn(mplot_sys,RooFit.Name("jer_dn"), RooFit.LineColor(6));

           if label == "_WJets0" and self.workspace4fit_.pdf("model_WJets01_%s_mj"%(self.channel)):
              self.workspace4fit_.pdf("model_WJets01_%s_mj"%(self.channel)).plotOn(mplot_sys,RooFit.Name("alt shape"), RooFit.LineColor(kOrange+1));

           self.leg = self.legend4Plot(mplot_sys,0,1,0., 0.06, 0.16, 0.);
           mplot_sys.addObject(self.leg);
           rdataset_mj.plotOn(mplot_sys, RooFit.Name("MC Events"), RooFit.MarkerSize(1.5), RooFit.DataError(RooAbsData.SumW2), RooFit.XErrorSize(0) );
           model_deco.plotOn(mplot_sys,RooFit.Name("Nominal MC"),RooFit.LineColor(kBlack));
           mplot_sys.GetYaxis().SetRangeUser(1e-2,mplot_sys.GetMaximum()*1.2);

#           self.draw_canvas(mplot_sys,"plots_%s_%s_%s_%s_g1/other/"%(options.additioninformation, self.channel,self.PS_model,self.wtagger_label),in_file_name,"m_j_shape"+label,0,1);
           self.draw_canvas_with_pull( mplot_sys, mplot_pull,parameters_list,"plots_%s_%s_%s_%s_g1/other/"%(options.additioninformation,self.channel,self.PS_model,self.wtagger_label),in_file_name,"m_j_shape"+label,in_model_name);

        print "####################################################";
        print "######## Normalization Factor in mJ ################"
        print "####################################################";

        #normalize the number of total events to lumi --> correct the number to scale to the lumi
        self.workspace4fit_.var("rrv_number"+label+"_"+self.channel+"_mj").setVal(self.workspace4fit_.var("rrv_number"+label+"_"+self.channel+"_mj").getVal()*self.workspace4fit_.var("rrv_scale_to_lumi"+label+"_"+self.channel).getVal() )
        self.workspace4fit_.var("rrv_number"+label+"_"+self.channel+"_mj").setError(self.workspace4fit_.var("rrv_number"+label+"_"+self.channel+"_mj").getError()*self.workspace4fit_.var("rrv_scale_to_lumi"+label+"_"+self.channel).getVal() )

        self.workspace4fit_.var("rrv_number"+label+"_"+self.channel+"_mj").Print();
        
           
        if TString(label).Contains("ggH"):
            self.workspace4fit_.var("rrv_number"+label+"_"+self.channel+"_mj").setVal( self.workspace4fit_.var("rrv_number"+label+"_"+self.channel+"_mj").getVal() )
            self.workspace4fit_.var("rrv_number"+label+"_"+self.channel+"_mj").setError(self.workspace4fit_.var("rrv_number"+label+"_"+self.channel+"_mj").getError() )
            self.workspace4fit_.var("rrv_number"+label+"_"+self.channel+"_mj").Print();

        if TString(label).Contains("vbfH"):
            self.workspace4fit_.var("rrv_number"+label+"_"+self.channel+"_mj").setVal( self.workspace4fit_.var("rrv_number"+label+"_"+self.channel+"_mj").getVal() )
            self.workspace4fit_.var("rrv_number"+label+"_"+self.channel+"_mj").setError(self.workspace4fit_.var("rrv_number"+label+"_"+self.channel+"_mj").getError() )
            self.workspace4fit_.var("rrv_number"+label+"_"+self.channel+"_mj").Print();

        ##### apply the correction of the mean and sigma from the ttbar control sample to the STop, TTbar and VV
        par=parameters_list.createIterator();
        par.Reset();
        param=par.Next()
        while (param):
              if (TString(label).Contains("VV") or TString(label).Contains("WW_EWK") or TString(label).Contains("STop") or TString(label).Contains("TTbar")):
                if TString(param.GetName()).Contains("rrv_mean1_gaus"):
                    param.setRange(param.getMin()+self.mean_shift, param.getMax()+self.mean_shift);
                    param.setVal(param.getVal()+self.mean_shift);
                if TString(param.GetName()).Contains("rrv_deltamean_gaus"):
                    param.setRange(param.getMin()-self.mean_shift, param.getMax()-self.mean_shift);
                    param.setVal(param.getVal()-self.mean_shift);
                if TString(param.GetName()).Contains("rrv_sigma1_gaus"):
                    param.setVal(param.getVal()*self.sigma_scale);
                    param.setRange(param.getMin()*self.sigma_scale, param.getMax()*self.sigma_scale);
                if TString(param.GetName()).Contains("rrv_scalesigma_gaus"):
                    param.setRange(param.getMin()/self.sigma_scale, param.getMax()/self.sigma_scale);
                    param.setVal(param.getVal()/self.sigma_scale);
              param=par.Next()


        if(rdataset_mj_relaxed):
            
         model_relaxed = self.make_Model(label,in_model_name,"_mj_relaxed");
         rfresult_relaxed = model_relaxed.fitTo(rdataset_mj_relaxed,RooFit.Save(1), RooFit.Extended(kTRUE),  RooFit.SumW2Error(kTRUE) );
         rfresult_relaxed = model_relaxed.fitTo(rdataset_mj_relaxed,RooFit.Save(1), RooFit.SumW2Error(kTRUE) ,RooFit.Extended(kTRUE), RooFit.Minimizer("Minuit2") );
         rfresult_relaxed = model_relaxed.fitTo(rdataset_mj_relaxed,RooFit.Save(1), RooFit.SumW2Error(kTRUE) ,RooFit.Extended(kTRUE), RooFit.Minimizer("Minuit2") );
         rfresult_relaxed.Print();
            
         ## Plot the result after relaxed cut
         mplot_relaxed = rrv_mass_j.frame(RooFit.Title(label+" fitted by "+in_model_name), RooFit.Bins(int(rrv_mass_j.getBins()/self.narrow_factor)) );
         rdataset_mj_relaxed.plotOn( mplot_relaxed, RooFit.MarkerSize(1.5), RooFit.DataError(RooAbsData.SumW2), RooFit.XErrorSize(0) );

 	 ## draw the error band for an extend pdf
         draw_error_band_extendPdf(rdataset_mj_relaxed, model_relaxed, rfresult_relaxed,mplot_relaxed,2,"L");
         ## re-draw the dataset
         rdataset_mj_relaxed.plotOn( mplot , RooFit.MarkerSize(1.5), RooFit.DataError(RooAbsData.SumW2), RooFit.XErrorSize(0) );
         ## draw the function
         model_relaxed.plotOn( mplot_relaxed );# remove RooFit.VLines() in order to get right pull in the 1st bin

         ## Get the pull
         mplot_pull_relaxed = self.get_pull(rrv_mass_j, mplot_relaxed);
         mplot_relaxed.GetYaxis().SetRangeUser(1e-5,mplot_relaxed.GetMaximum()*1.2);

         ##CALCULATE CHI2
         datahist_relaxed=rdataset_mj_relaxed.binnedClone(rdataset_mj_relaxed.GetName()+"_binnedClone",rdataset_mj_relaxed.GetName()+"_binnedClone")
         Nbin_relaxed = int(rrv_mass_j.getBins()); 
         rresult_relaxed_param = rfresult_relaxed.floatParsFinal();        
         nparameters_relaxed  =  rresult_relaxed_param.getSize()                                         
         ChiSquare_relaxed    = model_relaxed.createChi2(datahist_relaxed,RooFit.Extended(kTRUE),RooFit.DataError(RooAbsData.Poisson));
         chi_over_ndf_relaxed = ChiSquare_relaxed.getVal()/(Nbin_relaxed - nparameters_relaxed);

         ##Add Chisquare to mplot_pull
         cs2 = TLatex(0.75,0.8,"#chi^{2}/ndf = %0.2f "%(float(chi_over_ndf_relaxed)));
         cs2.SetNDC();
         cs2.SetTextSize(0.12);
         cs2.AppendPad("same");
         mplot_pull_relaxed.addObject(cs2)

         parameters_list_relaxed = model_relaxed.getParameters(rdataset_mj_relaxed);
         self.draw_canvas_with_pull( mplot_relaxed, mplot_pull_relaxed,parameters_list_relaxed,"plots_%s_%s_%s_%s_g1/m_j_fitting%s_wtaggercut%s_relaxed/"%(options.additioninformation, self.channel,self.PS_model, self.wtagger_label, additioninformation, self.wtagger_label), label+in_file_name, in_model_name)


         if label == "_STop" or label == "_VV" or label == "_WJets0" or label == "_WW_EWK" or label == "_TTbar" :

           mplot_sys = rrv_mass_j.frame( RooFit.Bins(int(rrv_mass_j.getBins()/self.narrow_factor)));
           rdataset_mj_relaxed.plotOn(mplot_sys, RooFit.Name("MC Events"), RooFit.MarkerSize(1.5), RooFit.DataError(RooAbsData.SumW2), RooFit.XErrorSize(0) );
           model_relaxed.plotOn(mplot_sys,RooFit.Name("Nominal MC"),RooFit.LineColor(kBlack));
           draw_error_band_extendPdf(rdataset_mj_relaxed, model_relaxed, rfresult_relaxed,mplot_sys,self.color_palet["Uncertainty"],"F");

           if self.workspace4fit_.pdf("model%smassvbf_jes_up_%s_mj_relaxed"%(label,self.channel)) :
              self.workspace4fit_.pdf("model%smassvbf_jes_up_%s_mj_relaxed"%(label,self.channel)).plotOn(mplot_sys,RooFit.Name("jes_up"), RooFit.LineColor(kRed),RooFit.Normalization(self.workspace4fit_.var("rrv_number"+label+"massvbf_jes_up_"+self.channel+"_mj_relaxed").getVal()/(self.workspace4fit_.var("rrv_vbf_cut_total"+label+"_"+self.channel).getVal()*rdataset_mj_relaxed.sumEntries()*self.workspace4fit_.var("rrv_scale_to_lumi"+label+"_"+self.channel).getVal())));

           if self.workspace4fit_.pdf("model%smassvbf_jes_dn_%s_mj_relaxed"%(label,self.channel)) :
              self.workspace4fit_.pdf("model%smassvbf_jes_dn_%s_mj_relaxed"%(label,self.channel)).plotOn(mplot_sys,RooFit.Name("jes_dn"), RooFit.LineColor(kBlue),RooFit.Normalization(self.workspace4fit_.var("rrv_number"+label+"massvbf_jes_dn_"+self.channel+"_mj_relaxed").getVal()/(self.workspace4fit_.var("rrv_vbf_cut_total"+label+"_"+self.channel).getVal()*rdataset_mj_relaxed.sumEntries()*self.workspace4fit_.var("rrv_scale_to_lumi"+label+"_"+self.channel).getVal())));

           if self.workspace4fit_.pdf("model%smassvbf_jer_%s_mj_relaxed"%(label,self.channel)) :
              self.workspace4fit_.pdf("model%smassvbf_jer_%s_mj_relaxed"%(label,self.channel)).plotOn(mplot_sys,RooFit.Name("jer"), RooFit.LineColor(kAzure+1),RooFit.Normalization(self.workspace4fit_.var("rrv_number"+label+"massvbf_jer_"+self.channel+"_mj_relaxed").getVal()/(self.workspace4fit_.var("rrv_vbf_cut_total"+label+"_"+self.channel).getVal()*rdataset_mj_relaxed.sumEntries()*self.workspace4fit_.var("rrv_scale_to_lumi"+label+"_"+self.channel).getVal())));

           if self.workspace4fit_.pdf("model%smassvbf_jer_up_%s_mj_relaxed"%(label,self.channel)) :
              self.workspace4fit_.pdf("model%smassvbf_jer_up_%s_mj_relaxed"%(label,self.channel)).plotOn(mplot_sys,RooFit.Name("jer_up"), RooFit.LineColor(kGreen+1),RooFit.Normalization(self.workspace4fit_.var("rrv_number"+label+"massvbf_jer_up_"+self.channel+"_mj_relaxed").getVal()/(self.workspace4fit_.var("rrv_vbf_cut_total"+label+"_"+self.channel).getVal()*rdataset_mj_relaxed.sumEntries()*self.workspace4fit_.var("rrv_scale_to_lumi"+label+"_"+self.channel).getVal())));

           if self.workspace4fit_.pdf("model%smassvbf_jer_dn_%s_mj_relaxed"%(label,self.channel)) :
              self.workspace4fit_.pdf("model%smassvbf_jer_up_%s_mj_relaxed"%(label,self.channel)).plotOn(mplot_sys,RooFit.Name("jer_dn"), RooFit.LineColor(6),RooFit.Normalization(self.workspace4fit_.var("rrv_number"+label+"massvbf_jer_dn_"+self.channel+"_mj_relaxed").getVal()/(self.workspace4fit_.var("rrv_vbf_cut_total"+label+"_"+self.channel).getVal()*rdataset_mj_relaxed.sumEntries()*self.workspace4fit_.var("rrv_scale_to_lumi"+label+"_"+self.channel).getVal())));

           if label == "_WJets0" and self.workspace4fit_.pdf("model_WJets01_%s_mj_relaxed"%(self.channel)):
              self.workspace4fit_.pdf("model_WJets01_%s_mj_relaxed"%(self.channel)).plotOn(mplot_sys,RooFit.Name("alt shape"), RooFit.LineColor(kOrange+1),RooFit.Normalization(self.workspace4fit_.var("rrv_number_WJets01_"+self.channel+"_mj_relaxed").getVal()/(rdataset_mj_relaxed.sumEntries()*self.workspace4fit_.var("rrv_vbf_cut_total"+label+"_"+self.channel).getVal()*self.workspace4fit_.var("rrv_scale_to_lumi"+label+"_"+self.channel).getVal())));

           self.leg = self.legend4Plot(mplot_sys,0,1,0., 0.06, 0.16, 0.);
           mplot_sys.addObject(self.leg);
           rdataset_mj_relaxed.plotOn(mplot_sys, RooFit.Name("MC Events"), RooFit.MarkerSize(1.5), RooFit.DataError(RooAbsData.SumW2), RooFit.XErrorSize(0) );
           model_relaxed.plotOn(mplot_sys,RooFit.Name("Nominal MC"),RooFit.LineColor(kBlack));
           mplot_sys.GetYaxis().SetRangeUser(1e-2,mplot_sys.GetMaximum()*1.2);
           
           self.draw_canvas_with_pull( mplot_sys, mplot_pull,parameters_list,"plots_%s_%s_%s_%s_g1/other/"%(options.additioninformation,self.channel,self.PS_model,self.wtagger_label),in_file_name,"m_j_relaxed_extended"+label,in_model_name);
#           self.draw_canvas(mplot_sys,"plots_%s_%s_%s_%s_g1/other/"%(options.additioninformation, self.channel,self.PS_model,self.wtagger_label),in_file_name,"m_j_extended_relaxed"+label,0,1);


           print "################### Decorrelated mj single mc shape ################"
           ## temp workspace for the pdf diagonalizer
           model_pdf = self.workspace4fit_.pdf("model_pdf%s_%s_mj_relaxed"%(label,self.channel)); ## take the pdf from the workspace
           model_pdf.fitTo(rdataset_mj_relaxed, RooFit.Save(1), RooFit.SumW2Error(kTRUE) );
           rfresult_pdf = model_pdf.fitTo( rdataset_mj_relaxed, RooFit.Save(1), RooFit.SumW2Error(kTRUE), RooFit.Minimizer("Minuit2"));
           wsfit_tmp = RooWorkspace("wsfit_tmp"+label+"_"+self.channel+"_mj_relaxed");
           Deco      = PdfDiagonalizer("Deco"+label+"_"+self.channel+"_"+self.wtagger_label+"_mj_relaxed",wsfit_tmp,rfresult_pdf); ## in order to have a good name
           print "##################### diagonalize ";
           model_deco = Deco.diagonalize(model_pdf); ## diagonalize
           print "##################### original  parameters ";
           model_pdf.getParameters(rdataset_mj_relaxed).Print("v");
           print "##################### original  decorrelated parameters ";
           model_deco.getParameters(rdataset_mj_relaxed).Print("v");
           print "##################### original  pdf ";
           model_pdf.Print();
           print "##################### decorrelated pdf ";
           model_deco.Print();

           mplot_sys = rrv_mass_j.frame( RooFit.Bins(int(rrv_mass_j.getBins()/self.narrow_factor)));
           rdataset_mj_relaxed.plotOn(mplot_sys, RooFit.Name("MC Events"), RooFit.MarkerSize(1.5), RooFit.DataError(RooAbsData.SumW2), RooFit.XErrorSize(0) );
           model_deco.plotOn(mplot_sys,RooFit.Name("Nominal MC"),RooFit.LineColor(kBlack));
           rrv_number_dataset = RooRealVar("rrv_number_dataset","rrv_number_dataset",rdataset_mj_relaxed.sumEntries());
           rrv_number_dataset.setError(0.); ## only shape uncertainty
           draw_error_band(rdataset_mj_relaxed, model_pdf,rrv_number_dataset,rfresult_pdf,mplot_sys,self.color_palet["Uncertainty"],"F"); ## draw the error band with the area

           if self.workspace4fit_.pdf("model%smassvbf_jes_up_%s_mj_relaxed"%(label,self.channel)) :
              self.workspace4fit_.pdf("model%smassvbf_jes_up_%s_mj_relaxed"%(label,self.channel)).plotOn(mplot_sys,RooFit.Name("jes_up"), RooFit.LineColor(kRed));

           if self.workspace4fit_.pdf("model%smassvbf_jes_dn_%s_mj_relaxed"%(label,self.channel)) :
              self.workspace4fit_.pdf("model%smassvbf_jes_dn_%s_mj_relaxed"%(label,self.channel)).plotOn(mplot_sys,RooFit.Name("jes_dn"), RooFit.LineColor(kBlue));

           if self.workspace4fit_.pdf("model%smassvbf_jer_%s_mj_relaxed"%(label,self.channel)) :
              self.workspace4fit_.pdf("model%smassvbf_jer_%s_mj_relaxed"%(label,self.channel)).plotOn(mplot_sys,RooFit.Name("jer"), RooFit.LineColor(kAzure+1));

           if self.workspace4fit_.pdf("model%smassvbf_jer_up_%s_mj_relaxed"%(label,self.channel)) :
              self.workspace4fit_.pdf("model%smassvbf_jer_up_%s_mj_relaxed"%(label,self.channel)).plotOn(mplot_sys,RooFit.Name("jer_up"), RooFit.LineColor(kGreen+1));

           if self.workspace4fit_.pdf("model%smassvbf_jer_dn_%s_mj_relaxed"%(label,self.channel)) :
              self.workspace4fit_.pdf("model%smassvbf_jer_up_%s_mj_relaxed"%(label,self.channel)).plotOn(mplot_sys,RooFit.Name("jer_dn"), RooFit.LineColor(6));

           if label == "_WJets0" and self.workspace4fit_.pdf("model_WJets01_%s_mj_relaxed"%(self.channel)):
              self.workspace4fit_.pdf("model_WJets01_%s_mj_relaxed"%(self.channel)).plotOn(mplot_sys,RooFit.Name("alt shape"), RooFit.LineColor(kOrange+1));

           self.leg = self.legend4Plot(mplot_sys,0,1,0., 0.06, 0.16, 0.);
           mplot_sys.addObject(self.leg);
           rdataset_mj_relaxed.plotOn(mplot_sys, RooFit.Name("MC Events"), RooFit.MarkerSize(1.5), RooFit.DataError(RooAbsData.SumW2), RooFit.XErrorSize(0) );
           model_pdf.plotOn(mplot_sys,RooFit.Name("Nominal MC"),RooFit.LineColor(kBlack));
           mplot_sys.GetYaxis().SetRangeUser(1e-2,mplot_sys.GetMaximum()*1.2);

           self.draw_canvas_with_pull( mplot_sys, mplot_pull,parameters_list,"plots_%s_%s_%s_%s_g1/other/"%(options.additioninformation,self.channel,self.PS_model,self.wtagger_label),in_file_name,"m_j_shape_relaxed"+label,in_model_name);
#           self.draw_canvas(mplot_sys,"plots_%s_%s_%s_%s_g1/other/"%(options.additioninformation, self.channel,self.PS_model,self.wtagger_label),in_file_name,"m_j_shape_relaxed"+label,0,1);

         ## Plot the result relaxed shap on dataset after cut
         mplot_same = rrv_mass_j.frame(RooFit.Title(label+" fitted by "+in_model_name), RooFit.Bins(int(rrv_mass_j.getBins()/self.narrow_factor)) );
         rdataset_mj.plotOn( mplot_same, RooFit.MarkerSize(1.5), RooFit.DataError(RooAbsData.SumW2), RooFit.XErrorSize(0) );

         par=parameters_list_relaxed.createIterator();
         par.Reset();
         param=par.Next()
         while (param):
             if TString(param.GetName()).Contains("number"):
                 param.setVal(param.getVal()*self.workspace4fit_.var("rrv_vbf_cut_total"+label+"_"+self.channel).getVal());
                 param.setError(param.getError()*self.workspace4fit_.var("rrv_vbf_cut_total"+label+"_"+self.channel).getVal());
                 param.Print();
             param=par.Next()
                 
         ## re-draw the dataset
         band_up = TGraph(); band_dn = TGraph();         
         band_up = mplot_relaxed.findObject("error_up");
         band_dn = mplot_relaxed.findObject("error_dn");
         
         for ipoint in range(0,band_up.GetN()) and range(0,band_dn.GetN()):
             x1 = ROOT.Double(0.) ; y1 = ROOT.Double(0.) ;
             band_up.GetPoint(ipoint,x1,y1);
             band_up.SetPoint(ipoint,x1,y1*self.workspace4fit_.var("rrv_vbf_cut_total"+label+"_"+self.channel).getVal());
             x2 = ROOT.Double(0.) ; y2 = ROOT.Double(0.) ;
             band_dn.GetPoint(ipoint,x2,y2);
             band_dn.SetPoint(ipoint,x2,y2*self.workspace4fit_.var("rrv_vbf_cut_total"+label+"_"+self.channel).getVal());
             
         mplot_same.addObject(band_up,"L");
         mplot_same.addObject(band_dn,"L"); 
        
         rdataset_mj.plotOn(mplot_same,RooFit.MarkerSize(1.5),RooFit.DataError(RooAbsData.SumW2),RooFit.XErrorSize(0));
         ## draw the function
         model.plotOn(mplot_same, RooFit.LineColor(1));
         model_relaxed.plotOn(mplot_same);# remove RooFit.VLines() in order to get right pull in the 1st bin

         ## Get the pull
         mplot_pull_same = self.get_pull(rrv_mass_j, mplot_same);
         mplot_same.GetYaxis().SetRangeUser(1e-5,mplot_same.GetMaximum()*1.2);

         ##CALCULATE CHI2
         Nbin = int(rrv_mass_j.getBins()); 
         ChiSquare_same = model_relaxed.createChi2(datahist,RooFit.Extended(kTRUE),RooFit.SumW2Error(kTRUE));
         chi_over_ndf_same= ChiSquare_same.getVal()/(Nbin - nparameters_relaxed);
                  
         ##Add Chisquare to mplot_pull
         cs3 = TLatex(0.75,0.8,"#chi^{2}/ndf = %0.2f "%(float(chi_over_ndf_same)));
         cs3.SetNDC();
         cs3.SetTextSize(0.12);
         cs3.AppendPad("same");
         mplot_pull_same.addObject(cs3)

         parameters_list_same = model_relaxed.getParameters(rdataset_mj);
         self.draw_canvas_with_pull( mplot_same, mplot_pull_same,parameters_list_same,"plots_%s_%s_%s_%s_g1/m_j_fitting%s_wtaggercut%s_same/"%(options.additioninformation, self.channel,self.PS_model, self.wtagger_label, additioninformation, self.wtagger_label), label+in_file_name, in_model_name)



         if(self.workspace4fit_.var("rrv_number"+label+"_"+self.channel+"_mj_relaxed")):
           self.workspace4fit_.var("rrv_number"+label+"_"+self.channel+"_mj_relaxed").setVal(self.workspace4fit_.var("rrv_number"+label+"_"+self.channel+"_mj_relaxed").getVal()*self.workspace4fit_.var("rrv_scale_to_lumi"+label+"_"+self.channel).getVal());
           self.workspace4fit_.var("rrv_number"+label+"_"+self.channel+"_mj_relaxed").setError(self.workspace4fit_.var("rrv_number"+label+"_"+self.channel+"_mj").getError());
           self.workspace4fit_.var("rrv_number"+label+"_"+self.channel+"_mj_relaxed").Print();
           
         if TString(label).Contains("ggH"):
            if self.workspace4fit_.var("rrv_number"+label+"_"+self.channel+"_mj_relaxed"):
               self.workspace4fit_.var("rrv_number"+label+"_"+self.channel+"_mj_relaxed").setVal(self.workspace4fit_.var("rrv_number"+label+"_"+self.channel+"_mj_relaxed").getVal());
               self.workspace4fit_.var("rrv_number"+label+"_"+self.channel+"_mj_relaxed").setError(self.workspace4fit_.var("rrv_number"+label+"_"+self.channel+"_mj").getError());
               self.workspace4fit_.var("rrv_number"+label+"_"+self.channel+"_mj_relaxed").Print();

         if TString(label).Contains("vbfH"):
            self.workspace4fit_.var("rrv_number"+label+"_"+self.channel+"_mj_relaxed").setVal( self.workspace4fit_.var("rrv_number"+label+"_"+self.channel+"_mj_relaxed").getVal() )
            self.workspace4fit_.var("rrv_number"+label+"_"+self.channel+"_mj_relaxed").setError(self.workspace4fit_.var("rrv_number"+label+"_"+self.channel+"_mj_relaxed").getError() )
            self.workspace4fit_.var("rrv_number"+label+"_"+self.channel+"_mj_relaxed").Print();


         par = parameters_list_relaxed.createIterator();
         par.Reset();
         param=par.Next()
         while (param):
              if (TString(label).Contains("VV") or TString(label).Contains("WW_EWK") or TString(label).Contains("STop") or TString(label).Contains("TTbar")):
                if TString(param.GetName()).Contains("rrv_mean1_gaus"):
                    param.setRange(param.getMin()+self.mean_shift, param.getMax()+self.mean_shift);
                    param.setVal(param.getVal()+self.mean_shift);
                if TString(param.GetName()).Contains("rrv_deltamean_gaus"):
                    param.setRange(param.getMin()-self.mean_shift, param.getMax()-self.mean_shift);
                    param.setVal(param.getVal()-self.mean_shift);
                if TString(param.GetName()).Contains("rrv_sigma1_gaus"):
                    param.setVal(param.getVal()*self.sigma_scale);
                    param.setRange(param.getMin()*self.sigma_scale, param.getMax()*self.sigma_scale);
                if TString(param.GetName()).Contains("rrv_scalesigma_gaus"):
                    param.setRange(param.getMin()/self.sigma_scale, param.getMax()/self.sigma_scale);
                    param.setVal(param.getVal()/self.sigma_scale);
              param=par.Next()
         
                         
 
    ### Define the Extended Pdf for and mlvj fit giving: label, fit model name, list constraint, range to be fitted and do the decorrelation
    def fit_mlvj_model_single_MC(self,in_file_name, label, in_range, mlvj_model, deco=0, show_constant_parameter=0, logy=0, ismc=0, label_origin=""):

        print "############### Fit mlvj single MC sample ",in_file_name," ",label,"  ",mlvj_model,"  ",in_range," ##################"
        ## import variable and dataset
        rrv_mass_lvj = self.workspace4fit_.var("rrv_mass_lvj")
        rdataset = self.workspace4fit_.data("rdataset4fit"+label+in_range+"_"+self.channel+"_mlvj");
	rdataset_relaxed = self.workspace4fit_.data("rdataset4fit"+label+in_range+"_"+self.channel+"_mlvj_relaxed");
        constrainslist =[];
        constrainslist_relaxed =[];

        ## make the extended pdf model
        model = self.make_Model(label+in_range,mlvj_model,"_mlvj",constrainslist,ismc);

        ## make the fit
        rfresult = model.fitTo( rdataset, RooFit.Save(1), RooFit.SumW2Error(kTRUE) ,RooFit.Extended(kTRUE) );
        rfresult = model.fitTo( rdataset, RooFit.Save(1), RooFit.SumW2Error(kTRUE) ,RooFit.Extended(kTRUE), RooFit.Minimizer("Minuit2") );
        rfresult.Print();

        ## set the name of the result of the fit and put it in the workspace
        rfresult.SetName("rfresult"+label+in_range+"_"+self.channel+"_mlvj")
        getattr(self.workspace4fit_,"import")(rfresult)

        ## plot the result
	mplot = rrv_mass_lvj.frame(RooFit.Title("M_{lvj"+in_range+"} fitted by "+mlvj_model), RooFit.Bins(int(rrv_mass_lvj.getBins()/self.narrow_factor)));
        rdataset.plotOn( mplot , RooFit.MarkerSize(1.5), RooFit.DataError(RooAbsData.SumW2), RooFit.XErrorSize(0) );
        ## plot the error band but don't store the canvas (only plotted without -b option
	draw_error_band_extendPdf(rdataset, model, rfresult,mplot,2,"L")
        rdataset.plotOn( mplot , RooFit.MarkerSize(1.5), RooFit.DataError(RooAbsData.SumW2), RooFit.XErrorSize(0) );
        model.plotOn( mplot )#, RooFit.VLines()); in order to have the right pull

        ## get the pull
	mplot_pull      = self.get_pull(rrv_mass_lvj,mplot);
        parameters_list = model.getParameters(rdataset);
        mplot.GetYaxis().SetRangeUser(1e-2,mplot.GetMaximum()*1.2);

        ##CALCULATE CHI2
        datahist = rdataset.binnedClone(rdataset.GetName()+"_binnedClone",rdataset.GetName()+"_binnedClone")
        Nbin     = int(rrv_mass_lvj.getBins()); 
        rresult_param = rfresult.floatParsFinal();        
        nparameters =  rresult_param.getSize()                                         
        ChiSquare = model.createChi2(datahist,RooFit.Extended(kTRUE),RooFit.DataError(RooAbsData.Poisson));
        chi_over_ndf= ChiSquare.getVal()/(Nbin - nparameters);

        ##Add Chisquare to mplot_pull
        cs = TLatex(0.75,0.8,"#chi^{2}/ndf = %0.2f "%(float(chi_over_ndf)));
        cs.SetNDC();
        cs.SetTextSize(0.12);
        cs.AppendPad("same");
        mplot_pull.addObject(cs)

        self.draw_canvas_with_pull( mplot, mplot_pull,parameters_list,"plots_%s_%s_%s_%s_g1/m_lvj_fitting/"%(options.additioninformation,self.channel,self.PS_model,self.wtagger_label),in_file_name,"m_lvj"+label+in_range+mlvj_model, show_constant_parameter, logy);


        if not TString(label).Contains("_jes") and not TString(label).Contains("_jer") :

           mplot_sys = rrv_mass_lvj.frame( RooFit.Bins(int(rrv_mass_lvj.getBins()/self.narrow_factor)));
           rdataset.plotOn(mplot_sys, RooFit.Name("MC Events"), RooFit.MarkerSize(1.5), RooFit.DataError(RooAbsData.SumW2), RooFit.XErrorSize(0) );
           model.plotOn(mplot_sys,RooFit.Name("Nominal MC"),RooFit.LineColor(kBlack))
           draw_error_band_extendPdf(rdataset, model, rfresult,mplot_sys,self.color_palet["Uncertainty"],"F");

           if self.channel != "el":               
            if self.workspace4fit_.pdf("model%smassvbf_jes_up%s_%s_mlvj"%(label,in_range,self.channel)) :
              self.workspace4fit_.pdf("model%smassvbf_jes_up%s_%s_mlvj"%(label,in_range,self.channel)).plotOn(mplot_sys,RooFit.Name("jes_up"), RooFit.LineColor(kRed),RooFit.Normalization(self.workspace4fit_.var("rrv_number"+label+"massvbf_jes_up"+in_range+"_"+self.channel+"_mlvj").getVal()/(rdataset.sumEntries()*self.workspace4fit_.var("rrv_scale_to_lumi"+label_origin+"_"+self.channel+in_range+"_mlvj").getVal())));

            if self.workspace4fit_.pdf("model%smassvbf_jes_dn%s_%s_mlvj"%(label,in_range,self.channel)) :
              self.workspace4fit_.pdf("model%smassvbf_jes_dn%s_%s_mlvj"%(label,in_range,self.channel)).plotOn(mplot_sys,RooFit.Name("jes_dn"), RooFit.LineColor(kBlue),RooFit.Normalization(self.workspace4fit_.var("rrv_number"+label+"massvbf_jes_dn"+in_range+"_"+self.channel+"_mlvj").getVal()/(rdataset.sumEntries()*self.workspace4fit_.var("rrv_scale_to_lumi"+label_origin+"_"+self.channel+in_range+"_mlvj").getVal())));

            if self.workspace4fit_.pdf("model%smassvbf_jer%s_%s_mlvj"%(label,in_range,self.channel)) :
              self.workspace4fit_.pdf("model%smassvbf_jer%s_%s_mlvj"%(label,in_range,self.channel)).plotOn(mplot_sys,RooFit.Name("jer"), RooFit.LineColor(kAzure+1),RooFit.Normalization(self.workspace4fit_.var("rrv_number"+label+"massvbf_jer"+in_range+"_"+self.channel+"_mlvj").getVal()/(rdataset.sumEntries()*self.workspace4fit_.var("rrv_scale_to_lumi"+label_origin+"_"+self.channel+in_range+"_mlvj").getVal())));

            if self.workspace4fit_.pdf("model%smassvbf_jer_up%s_%s_mlvj"%(label,in_range,self.channel)) :
              self.workspace4fit_.pdf("model%smassvbf_jer_up%s_%s_mlvj"%(label,in_range,self.channel)).plotOn(mplot_sys,RooFit.Name("jer_up"), RooFit.LineColor(kGreen+1),RooFit.Normalization(self.workspace4fit_.var("rrv_number"+label+"massvbf_jer_up"+in_range+"_"+self.channel+"_mlvj").getVal()/(rdataset.sumEntries()*self.workspace4fit_.var("rrv_scale_to_lumi"+label_origin+"_"+self.channel+in_range+"_mlvj").getVal())));

            if self.workspace4fit_.pdf("model%smassvbf_jer_dn%s_%s_mlvj"%(label,in_range,self.channel)) :
              self.workspace4fit_.pdf("model%smassvbf_jer_dn%s_%s_mlvj"%(label,in_range,self.channel)).plotOn(mplot_sys,RooFit.Name("jer_dn"), RooFit.LineColor(6),RooFit.Normalization(self.workspace4fit_.var("rrv_number"+label+"massvbf_jer_dn"+in_range+"_"+self.channel+"_mlvj").getVal()/(rdataset.sumEntries()*self.workspace4fit_.var("rrv_scale_to_lumi"+label_origin+"_"+self.channel+in_range+"_mlvj").getVal())));

            if label == "_WJets0" and self.workspace4fit_.pdf("model_WJets01%s_%s_mlvj"%(in_range,self.channel)):
              self.workspace4fit_.pdf("model_WJets01%s_%s_mlvj"%(in_range,self.channel)).plotOn(mplot_sys,RooFit.Name("alt shape"), RooFit.LineColor(kOrange+1),RooFit.Normalization(self.workspace4fit_.var("rrv_number_WJets01"+in_range+"_"+self.channel+"_mlvj").getVal()/(rdataset.sumEntries()*self.workspace4fit_.var("rrv_scale_to_lumi"+label_origin+"_"+self.channel+in_range+"_mlvj").getVal())));


           self.leg = self.legend4Plot(mplot_sys,0,1,0., 0.06, 0.16, 0.);
           mplot_sys.addObject(self.leg);
           rdataset.plotOn(mplot_sys, RooFit.Name("MC Events"), RooFit.MarkerSize(1.5), RooFit.DataError(RooAbsData.SumW2), RooFit.XErrorSize(0) );
           model.plotOn(mplot_sys,RooFit.Name("Nominal MC"),RooFit.LineColor(kBlack));
           mplot_sys.GetYaxis().SetRangeUser(1e-2,mplot_sys.GetMaximum()*1.2);

           self.draw_canvas_with_pull( mplot_sys, mplot_pull,parameters_list,"plots_%s_%s_%s_%s_g1/other/"%(options.additioninformation,self.channel,self.PS_model,self.wtagger_label),in_file_name,"m_lvj_extended"+label+in_range+mlvj_model, show_constant_parameter, logy);
#           self.draw_canvas(mplot_sys,"plots_%s_%s_%s_%s_g1/other/"%(options.additioninformation, self.channel,self.PS_model,self.wtagger_label),in_file_name,"m_lvj_extended"+label,0,1);

           print "################### Decorrelated mlvj single mc shape ################"
           model_pdf = self.workspace4fit_.pdf("model_pdf%s%s_%s_mlvj"%(label,in_range,self.channel)); ## take the pdf from the workspace
           model_pdf.fitTo(rdataset, RooFit.Save(1), RooFit.SumW2Error(kTRUE) );
           rfresult_pdf = model_pdf.fitTo( rdataset, RooFit.Save(1), RooFit.SumW2Error(kTRUE), RooFit.Minimizer("Minuit2"));

           ## temp workspace for the pdf diagonalizer
           wsfit_tmp = RooWorkspace("wsfit_tmp"+label+in_range+"_"+self.channel+"_mlvj");
           Deco      = PdfDiagonalizer("Deco"+label+in_range+"_"+self.channel+"_"+self.wtagger_label+"_mlvj",wsfit_tmp,rfresult_pdf); ## in order to have a good name
           print "##################### diagonalize ";
           model_pdf_deco = Deco.diagonalize(model_pdf); ## diagonalize
           print "##################### workspace for decorrelation ";
           wsfit_tmp.Print("v");
           print "##################### original  parameters ";
           model_pdf.getParameters(rdataset).Print("v");
           print "##################### original  decorrelated parameters ";
           model_pdf_deco.getParameters(rdataset).Print("v");
           print "##################### original  pdf ";
           model_pdf.Print();
           print "##################### decorrelated pdf ";
           model_pdf_deco.Print();

           ## import in the workspace and print the diagonalizerd pdf
           if deco: getattr(self.workspace4fit_,"import")(model_pdf_deco);

           if label == "_TTbar" : #all the mc are normalized to the dataset just to appreciate shape variations

               mplot_deco = rrv_mass_lvj.frame( RooFit.Bins(int(rrv_mass_lvj.getBins()/self.narrow_factor)));
               rdataset.plotOn(mplot_deco, RooFit.Name("Powheg Sample"), RooFit.MarkerSize(1.5), RooFit.DataError(RooAbsData.SumW2), RooFit.XErrorSize(0) );
               model_pdf_deco.plotOn(mplot_deco,RooFit.Name("TTbar_Powheg"),RooFit.LineColor(kBlack));
               rrv_number_dataset = RooRealVar("rrv_number_dataset","rrv_number_dataset",rdataset.sumEntries());
               rrv_number_dataset.setError(0.); ## only shape uncertainty
               draw_error_band(rdataset, model_pdf,rrv_number_dataset,rfresult_pdf,mplot_deco,self.color_palet["Uncertainty"],"F"); ## draw the error band with the area

               if self.workspace4fit_.pdf("model%s_mcanlo%s_%s_mlvj"%(label,in_range,self.channel)) :
                  self.workspace4fit_.pdf("model%s_mcanlo%s_%s_mlvj"%(label,in_range,self.channel)).plotOn(mplot_deco,RooFit.Name("TTbar_mcanlo"), RooFit.LineColor(kBlue));

               if self.workspace4fit_.pdf("model%smassvbf_jes_up%s_%s_mlvj"%(label,in_range,self.channel)) :
                  self.workspace4fit_.pdf("model%smassvbf_jes_up%s_%s_mlvj"%(label,in_range,self.channel)).plotOn(mplot_deco,RooFit.Name("TTbar_jes_up"), RooFit.LineColor(kRed));

               if self.workspace4fit_.pdf("model%smassvbf_jes_dn%s_%s_mlvj"%(label,in_range,self.channel)) :
                  self.workspace4fit_.pdf("model%smassvbf_jes_dn%s_%s_mlvj"%(label,in_range,self.channel)).plotOn(mplot_deco,RooFit.Name("TTbar_jes_dn"), RooFit.LineColor(kAzure+1));

               if self.workspace4fit_.pdf("model%smassvbf_jer%s_%s_mlvj"%(label,in_range,self.channel)) :
                  self.workspace4fit_.pdf("model%smassvbf_jer%s_%s_mlvj"%(label,in_range,self.channel)).plotOn(mplot_deco,RooFit.Name("TTbar_jer"), RooFit.LineColor(kGreen+1));

               if self.workspace4fit_.pdf("model%smassvbf_jer_up%s_%s_mlvj"%(label,in_range,self.channel)) :
                  self.workspace4fit_.pdf("model%smassvbf_jer_up%s_%s_mlvj"%(label,in_range,self.channel)).plotOn(mplot_deco,RooFit.Name("TTbar_jer_up"), RooFit.LineColor(6));

               if self.workspace4fit_.pdf("model%smassvbf_jer_dn%s_%s_mlvj"%(label,in_range,self.channel)) :
                  self.workspace4fit_.pdf("model%smassvbf_jer_dn%s_%s_mlvj"%(label,in_range,self.channel)).plotOn(mplot_deco,RooFit.Name("TTbar_jer_dn"), RooFit.LineColor(kOrange+1));

               self.leg = self.legend4Plot(mplot_deco,0,1,0., 0.06, 0.16, 0.);
               mplot_deco.addObject(self.leg);
               rdataset.plotOn(mplot_deco, RooFit.Name("MC Events"), RooFit.MarkerSize(1.5), RooFit.DataError(RooAbsData.SumW2), RooFit.XErrorSize(0) );
               model_pdf.plotOn(mplot_deco,RooFit.Name("Nominal MC"),RooFit.LineColor(kBlack));
               mplot_deco.GetYaxis().SetRangeUser(1e-2,mplot_deco.GetMaximum()*1.2);

               self.draw_canvas_with_pull( mplot_deco, mplot_pull,parameters_list,"plots_%s_%s_%s_%s_g1/other/"%(options.additioninformation,self.channel,self.PS_model,self.wtagger_label),in_file_name,"m_lvj_shape"+label+in_range+mlvj_model, show_constant_parameter, logy);
#              self.draw_canvas(mplot_sys,"plots_%s_%s_%s_%s_g1/other/"%(options.additioninformation, self.channel,self.PS_model,self.wtagger_label),in_file_name,"m_lvj_shape"+label,0,1);

           else:

              mplot_deco = rrv_mass_lvj.frame( RooFit.Bins(int(rrv_mass_lvj.getBins()/self.narrow_factor)));
              rdataset.plotOn(mplot_deco, RooFit.Name("MC Events"), RooFit.MarkerSize(1.5), RooFit.DataError(RooAbsData.SumW2), RooFit.XErrorSize(0) );
              model_pdf.plotOn(mplot_deco,RooFit.Name("Nominal MC"),RooFit.LineColor(kBlack))
              rrv_number_dataset = RooRealVar("rrv_number_dataset","rrv_number_dataset",rdataset.sumEntries());
              rrv_number_dataset.setError(0.); ## only shape uncertainty
              draw_error_band(rdataset, model_pdf,rrv_number_dataset,rfresult_pdf,mplot_deco,self.color_palet["Uncertainty"],"F"); ## draw the error band with the area
           
              if self.workspace4fit_.pdf("model%smassvbf_jes_up%s_%s_mlvj"%(label,in_range,self.channel)) :
                 self.workspace4fit_.pdf("model%smassvbf_jes_up%s_%s_mlvj"%(label,in_range,self.channel)).plotOn(mplot_deco,RooFit.Name("jes_up"), RooFit.LineColor(kRed));

              if self.workspace4fit_.pdf("model%smassvbf_jes_dn%s_%s_mlvj"%(label,in_range,self.channel)) :
                 self.workspace4fit_.pdf("model%smassvbf_jes_dn%s_%s_mlvj"%(label,in_range,self.channel)).plotOn(mplot_deco,RooFit.Name("jes_dn"), RooFit.LineColor(kBlue));

              if self.workspace4fit_.pdf("model%smassvbf_jer%s_%s_mlvj"%(label,in_range,self.channel)) :
                 self.workspace4fit_.pdf("model%smassvbf_jer%s_%s_mlvj"%(label,in_range,self.channel)).plotOn(mplot_deco,RooFit.Name("jer"), RooFit.LineColor(kAzure+1));

              if self.workspace4fit_.pdf("model%smassvbf_jer_up%s_%s_mlvj"%(label,in_range,self.channel)) :
                 self.workspace4fit_.pdf("model%smassvbf_jer_up%s_%s_mlvj"%(label,in_range,self.channel)).plotOn(mplot_deco,RooFit.Name("jer_up"), RooFit.LineColor(kGreen+1));

              if self.workspace4fit_.pdf("model%smassvbf_jer_dn%s_%s_mlvj"%(label,in_range,self.channel)) :
                 self.workspace4fit_.pdf("model%smassvbf_jer_dn%s_%s_mlvj"%(label,in_range,self.channel)).plotOn(mplot_deco,RooFit.Name("jer_dn"), RooFit.LineColor(6));

              if label == "_WJets0" and self.workspace4fit_.pdf("model_WJets01%s_%s_mlvj"%(in_range,self.channel)):
                 self.workspace4fit_.pdf("model_WJets01%s_%s_mlvj"%(in_range,self.channel)).plotOn(mplot_sys,RooFit.Name("alt shape"), RooFit.LineColor(kOrange+1));

              self.leg = self.legend4Plot(mplot_deco,0,1,0., 0.06, 0.16, 0.);
              mplot_deco.addObject(self.leg);
              rdataset.plotOn(mplot_deco, RooFit.Name("MC Events"), RooFit.MarkerSize(1.5), RooFit.DataError(RooAbsData.SumW2), RooFit.XErrorSize(0) );
              model_pdf.plotOn(mplot_deco,RooFit.Name("Nominal MC"),RooFit.LineColor(kBlack));
              mplot_deco.GetYaxis().SetRangeUser(1e-2,mplot_deco.GetMaximum()*1.2);

              self.draw_canvas_with_pull( mplot_deco, mplot_pull,parameters_list,"plots_%s_%s_%s_%s_g1/other/"%(options.additioninformation,self.channel,self.PS_model,self.wtagger_label),in_file_name,"m_lvj_shape"+label+in_range+mlvj_model, show_constant_parameter, logy);
              #self.draw_canvas(mplot_sys,"plots_%s_%s_%s_%s_g1/other/"%(options.additioninformation, self.channel,self.PS_model,self.wtagger_label),in_file_name,"m_lvj_shape"+label,0,1);

        ### Number of the event in the dataset and lumi scale factor --> set the proper number for bkg extraction or for signal region
        self.workspace4fit_.var("rrv_number"+label+in_range+"_"+self.channel+"_mlvj").setVal(self.workspace4fit_.var("rrv_number"+label+in_range+"_"+self.channel+"_mlvj").getVal()*self.workspace4fit_.var("rrv_scale_to_lumi"+label_origin+"_"+self.channel+in_range+"_mlvj").getVal());
        self.workspace4fit_.var("rrv_number"+label+in_range+"_"+self.channel+"_mlvj").setError(self.workspace4fit_.var("rrv_number"+label+in_range+"_"+self.channel+"_mlvj").getError()*self.workspace4fit_.var("rrv_scale_to_lumi"+label_origin+"_"+self.channel+in_range+"_mlvj").getVal() );

        self.workspace4fit_.var("rrv_number"+label+in_range+"_"+self.channel+"_mlvj").Print();

        if rdataset_relaxed:            

         ## make the extended pdf model
         model_relaxed = self.make_Model(label+in_range,mlvj_model,"_mlvj_relaxed",constrainslist_relaxed,ismc);

         ## make the fit
         rfresult_relaxed = model_relaxed.fitTo( rdataset_relaxed, RooFit.Save(1), RooFit.SumW2Error(kTRUE) ,RooFit.Extended(kTRUE) );
         rfresult_relaxed = model_relaxed.fitTo( rdataset_relaxed, RooFit.Save(1), RooFit.SumW2Error(kTRUE) ,RooFit.Extended(kTRUE), RooFit.Minimizer("Minuit2") );
         rfresult_relaxed.Print();

         ## plot the result
	 mplot_relaxed = rrv_mass_lvj.frame(RooFit.Title("M_{lvj"+in_range+"} fitted by "+mlvj_model), RooFit.Bins(int(rrv_mass_lvj.getBins()/self.narrow_factor)));
         rdataset_relaxed.plotOn( mplot_relaxed , RooFit.MarkerSize(1.5), RooFit.DataError(RooAbsData.SumW2), RooFit.XErrorSize(0) );
         ## plot the error band but don't store the canvas (only plotted without -b option
	 draw_error_band_extendPdf(rdataset_relaxed, model_relaxed, rfresult_relaxed,mplot_relaxed,2,"L")
         rdataset_relaxed.plotOn( mplot_relaxed , RooFit.MarkerSize(1.5), RooFit.DataError(RooAbsData.SumW2), RooFit.XErrorSize(0) );
         model_relaxed.plotOn( mplot_relaxed )#, RooFit.VLines()); in order to have the right pull

         ## get the pull
	 mplot_pull_relaxed      = self.get_pull(rrv_mass_lvj,mplot_relaxed);
         parameters_list_relaxed = model_relaxed.getParameters(rdataset_relaxed);
         mplot_relaxed.GetYaxis().SetRangeUser(1e-5,mplot_relaxed.GetMaximum()*1.2);

         ##CALCULATE CHI2
         datahist_relaxed = rdataset_relaxed.binnedClone(rdataset_relaxed.GetName()+"_binnedClone",rdataset_relaxed.GetName()+"_binnedClone")
         Nbin_relaxed = int(rrv_mass_lvj.getBins()); 
         rresult_relaxed_param = rfresult_relaxed.floatParsFinal();        
         nparameters_relaxed =  rresult_relaxed_param.getSize()                                         
         ChiSquare_relaxed = model_relaxed.createChi2(datahist_relaxed,RooFit.Extended(kTRUE),RooFit.DataError(RooAbsData.Poisson));
         chi_over_ndf_relaxed = ChiSquare_relaxed.getVal()/(Nbin_relaxed - nparameters_relaxed);

         ##Add Chisquare to mplot_pull
         cs2 = TLatex(0.75,0.8,"#chi^{2}/ndf = %0.2f "%(float(chi_over_ndf_relaxed)));
         cs2.SetNDC();
         cs2.SetTextSize(0.12);
         cs2.AppendPad("same");
         mplot_pull_relaxed.addObject(cs2)

         self.draw_canvas_with_pull( mplot_relaxed, mplot_pull_relaxed,parameters_list_relaxed,"plots_%s_%s_%s_%s_g1/m_lvj_fitting_relaxed/"%(options.additioninformation,self.channel,self.PS_model,self.wtagger_label),in_file_name,"m_lvj"+label+in_range+mlvj_model, show_constant_parameter, logy);

         ## plot the result
         normalization = self.workspace4fit_.var("rrv_vbf_cut"+in_range+label+"_"+self.channel).getVal();

         if not TString(label).Contains("_jes") and not TString(label).Contains("_jer") :
             
           mplot_sys = rrv_mass_lvj.frame( RooFit.Bins(int(rrv_mass_lvj.getBins()/self.narrow_factor)));
           rdataset_relaxed.plotOn(mplot_sys, RooFit.Name("MC Events"), RooFit.MarkerSize(1.5), RooFit.DataError(RooAbsData.SumW2), RooFit.XErrorSize(0) );
           model_relaxed.plotOn(mplot_sys,RooFit.Name("Nominal MC"),RooFit.LineColor(kBlack));

           draw_error_band_extendPdf(rdataset_relaxed, model_relaxed, rfresult_relaxed,mplot_sys,self.color_palet["Uncertainty"],"F");

           if self.channel != "el": 
            if self.workspace4fit_.pdf("model%smassvbf_jes_up%s_%s_mlvj_relaxed"%(label,in_range,self.channel)) :               
              self.workspace4fit_.pdf("model%smassvbf_jes_up%s_%s_mlvj_relaxed"%(label,in_range,self.channel)).plotOn(mplot_sys,RooFit.Name("jes_up"), RooFit.LineColor(kRed),RooFit.Normalization(self.workspace4fit_.var("rrv_number"+label+"massvbf_jes_up"+in_range+"_"+self.channel+"_mlvj_relaxed").getVal()/(self.workspace4fit_.var("rrv_vbf_cut"+in_range+label+"massvbf_jes_up_"+self.channel).getVal()*rdataset_relaxed.sumEntries()*self.workspace4fit_.var("rrv_scale_to_lumi"+label_origin+"_"+self.channel+in_range+"_mlvj").getVal())));

            if self.workspace4fit_.pdf("model%smassvbf_jes_dn%s_%s_mlvj_relaxed"%(label,in_range,self.channel)) :
              self.workspace4fit_.pdf("model%smassvbf_jes_dn%s_%s_mlvj_relaxed"%(label,in_range,self.channel)).plotOn(mplot_sys,RooFit.Name("jes_dn"), RooFit.LineColor(kBlue),RooFit.Normalization(self.workspace4fit_.var("rrv_number"+label+"massvbf_jes_dn"+in_range+"_"+self.channel+"_mlvj_relaxed").getVal()/(self.workspace4fit_.var("rrv_vbf_cut"+in_range+label+"massvbf_jes_dn_"+self.channel).getVal()*rdataset_relaxed.sumEntries()*self.workspace4fit_.var("rrv_scale_to_lumi"+label_origin+"_"+self.channel+in_range+"_mlvj").getVal())));

            if self.workspace4fit_.pdf("model%smassvbf_jer%s_%s_mlvj_relaxed"%(label,in_range,self.channel)) :
              self.workspace4fit_.pdf("model%smassvbf_jer%s_%s_mlvj_relaxed"%(label,in_range,self.channel)).plotOn(mplot_sys,RooFit.Name("jer"), RooFit.LineColor(kAzure+1),RooFit.Normalization(self.workspace4fit_.var("rrv_number"+label+"massvbf_jer"+in_range+"_"+self.channel+"_mlvj_relaxed").getVal()/(self.workspace4fit_.var("rrv_vbf_cut"+in_range+label+"massvbf_jer_"+self.channel).getVal()*rdataset_relaxed.sumEntries()*self.workspace4fit_.var("rrv_scale_to_lumi"+label_origin+"_"+self.channel+in_range+"_mlvj").getVal())));

            if self.workspace4fit_.pdf("model%smassvbf_jer_up%s_%s_mlvj_relaxed"%(label,in_range,self.channel)) :
              self.workspace4fit_.pdf("model%smassvbf_jer_up%s_%s_mlvj_relaxed"%(label,in_range,self.channel)).plotOn(mplot_sys,RooFit.Name("jer_up"), RooFit.LineColor(kGreen+1),RooFit.Normalization(self.workspace4fit_.var("rrv_number"+label+"massvbf_jer_up"+in_range+"_"+self.channel+"_mlvj_relaxed").getVal()/(self.workspace4fit_.var("rrv_vbf_cut"+in_range+label+"massvbf_jer_up_"+self.channel).getVal()*rdataset_relaxed.sumEntries()*self.workspace4fit_.var("rrv_scale_to_lumi"+label_origin+"_"+self.channel+in_range+"_mlvj").getVal())));

            if self.workspace4fit_.pdf("model%smassvbf_jer_dn%s_%s_mlvj_relaxed"%(label,in_range,self.channel)) :
              self.workspace4fit_.pdf("model%smassvbf_jer_dn%s_%s_mlvj_relaxed"%(label,in_range,self.channel)).plotOn(mplot_sys,RooFit.Name("jer_dn"), RooFit.LineColor(6),RooFit.Normalization(self.workspace4fit_.var("rrv_number"+label+"massvbf_jer_dn"+in_range+"_"+self.channel+"_mlvj_relaxed").getVal()/(self.workspace4fit_.var("rrv_vbf_cut"+in_range+label+"massvbf_jer_dn_"+self.channel).getVal()*rdataset_relaxed.sumEntries()*self.workspace4fit_.var("rrv_scale_to_lumi"+label_origin+"_"+self.channel+in_range+"_mlvj").getVal())));

            if label == "_WJets0" and self.workspace4fit_.pdf("model_WJets01%s_%s_mlvj_relaxed"%(in_range,self.channel)):
              self.workspace4fit_.pdf("model_WJets01%s_%s_mlvj_relaxed"%(in_range,self.channel)).plotOn(mplot_sys,RooFit.Name("alt shape"), RooFit.LineColor(kOrange+1),RooFit.Normalization(self.workspace4fit_.var("rrv_number"+"_WJets01"+in_range+"_"+self.channel+"_mlvj_relaxed").getVal()/(self.workspace4fit_.var("rrv_vbf_cut"+in_range+"_WJets01_"+self.channel).getVal()*rdataset_relaxed.sumEntries()*self.workspace4fit_.var("rrv_scale_to_lumi"+label_origin+"_"+self.channel+in_range+"_mlvj").getVal())));

           self.leg = self.legend4Plot(mplot_sys,0,1,0., 0.06, 0.16, 0.);
           mplot_sys.addObject(self.leg);
           rdataset_relaxed.plotOn(mplot_sys, RooFit.Name("MC Events"), RooFit.MarkerSize(1.5), RooFit.DataError(RooAbsData.SumW2), RooFit.XErrorSize(0) );
           model_relaxed.plotOn(mplot_sys,RooFit.Name("Nominal MC"),RooFit.LineColor(kBlack));
           mplot_sys.GetYaxis().SetRangeUser(1e-2,mplot_sys.GetMaximum()*1.2);
           
#           self.draw_canvas(mplot_sys,"plots_%s_%s_%s_%s_g1/other/"%(options.additioninformation, self.channel,self.PS_model,self.wtagger_label),in_file_name,"m_lvj_extended_relaxed"+label,0,1);
           self.draw_canvas_with_pull( mplot_sys, mplot_pull,parameters_list,"plots_%s_%s_%s_%s_g1/other/"%(options.additioninformation,self.channel,self.PS_model,self.wtagger_label),in_file_name,"m_lvj_extended_relaxed"+label+in_range+mlvj_model, show_constant_parameter, logy);


           print "################### Decorrelated mlvj single mc relaxed shape ################"
           model_pdf_relaxed = self.workspace4fit_.pdf("model_pdf%s%s_%s_mlvj_relaxed"%(label,in_range,self.channel)); ## take the pdf from the workspace
           model_pdf_relaxed.fitTo( rdataset_relaxed, RooFit.Save(1), RooFit.SumW2Error(kTRUE) );
           rfresult_pdf_relaxed = model_pdf_relaxed.fitTo( rdataset_relaxed, RooFit.Save(1), RooFit.SumW2Error(kTRUE), RooFit.Minimizer("Minuit2"));
           rfresult_pdf_relaxed.Print();

           ## temp workspace for the pdf diagonalizer
           wsfit_tmp = RooWorkspace("wsfit_tmp"+label+in_range+"_"+self.channel+"_mlvj_relaxed");
           Deco = PdfDiagonalizer("Deco"+label+in_range+"_"+self.channel+"_"+self.wtagger_label+"_mlvj_relaxed",wsfit_tmp,rfresult_pdf_relaxed); ## in order to have a good name
           print "##################### diagonalize ";
           model_pdf_deco_relaxed = Deco.diagonalize(model_pdf_relaxed); ## diagonalize
           print "##################### workspace for decorrelation ";
           wsfit_tmp.Print("v");
           print "##################### original  parameters relaxed ";
           model_pdf_relaxed.getParameters(rdataset_relaxed).Print("v");
           print "##################### original  decorrelated parameters relaxed ";
           model_pdf_deco_relaxed.getParameters(rdataset_relaxed).Print("v");
           print "##################### original  pdf relaxed";
           model_pdf_relaxed.Print();
           print "##################### decorrelated pdf relaxed";
           model_pdf_deco_relaxed.Print();

           ## import in the workspace and print the diagonalizerd pdf
           if deco: getattr(self.workspace4fit_,"import")(model_pdf_deco_relaxed);

           ### define a frame for TTbar or other plots
           mplot_deco = rrv_mass_lvj.frame( RooFit.Bins(int(rrv_mass_lvj.getBins()/self.narrow_factor)));

           if label == "_TTbar" : #all the mc are normalized to the dataset just to appreciate shape variations

            rdataset_relaxed.plotOn(mplot_deco, RooFit.Name("Powheg Sample"), RooFit.MarkerSize(1.5), RooFit.DataError(RooAbsData.SumW2), RooFit.XErrorSize(0) );
            model_pdf_deco_relaxed.plotOn(mplot_deco,RooFit.Name("TTbar_Powheg"),RooFit.LineColor(kBlack));
            rrv_number_dataset = RooRealVar("rrv_number_dataset","rrv_number_dataset",rdataset_relaxed.sumEntries());
            rrv_number_dataset.setError(0.); ## only shape uncertainty
            draw_error_band(rdataset_relaxed, model_pdf_relaxed,rrv_number_dataset,rfresult_pdf_relaxed,mplot_deco,self.color_palet["Uncertainty"],"F"); ## draw the error band with the area

            if self.workspace4fit_.pdf("model%s_mcanlo%s_%s_mlvj_relaxed"%(label,in_range,self.channel)) :
               self.workspace4fit_.pdf("model%s_mcanlo%s_%s_mlvj_relaxed"%(label,in_range,self.channel)).plotOn(mplot_deco,RooFit.Name("TTbar_mcanlo"), RooFit.LineColor(kBlue));

            if self.workspace4fit_.pdf("model%smassvbf_jes_up%s_%s_mlvj_relaxed"%(label,in_range,self.channel)) :
               self.workspace4fit_.pdf("model%smassvbf_jes_up%s_%s_mlvj_relaxed"%(label,in_range,self.channel)).plotOn(mplot_deco,RooFit.Name("TTbar_jes_up"), RooFit.LineColor(kRed));

            if self.workspace4fit_.pdf("model%smassvbf_jes_dn%s_%s_mlvj_relaxed"%(label,in_range,self.channel)) :
               self.workspace4fit_.pdf("model%smassvbf_jes_dn%s_%s_mlvj_relaxed"%(label,in_range,self.channel)).plotOn(mplot_deco,RooFit.Name("TTbar_jes_dn"), RooFit.LineColor(kAzure+1));

            if self.workspace4fit_.pdf("model%smassvbf_jer%s_%s_mlvj_relaxed"%(label,in_range,self.channel)) :
               self.workspace4fit_.pdf("model%smassvbf_jer%s_%s_mlvj_relaxed"%(label,in_range,self.channel)).plotOn(mplot_deco,RooFit.Name("TTbar_jer"), RooFit.LineColor(kGreen+1));

            if self.workspace4fit_.pdf("model%smassvbf_jer_up%s_%s_mlvj_relaxed"%(label,in_range,self.channel)) :
               self.workspace4fit_.pdf("model%smassvbf_jer_up%s_%s_mlvj_relaxed"%(label,in_range,self.channel)).plotOn(mplot_deco,RooFit.Name("TTbar_jer_up"), RooFit.LineColor(6));

            if self.workspace4fit_.pdf("model%smassvbf_jer_dn%s_%s_mlvj_relaxed"%(label,in_range,self.channel)) :
               self.workspace4fit_.pdf("model%smassvbf_jer_dn%s_%s_mlvj_relaxed"%(label,in_range,self.channel)).plotOn(mplot_deco,RooFit.Name("TTbar_jer_dn"), RooFit.LineColor(kOrange+1));

           else:

            rdataset_relaxed.plotOn(mplot_deco, RooFit.Name("MC Events"), RooFit.MarkerSize(1.5), RooFit.DataError(RooAbsData.SumW2), RooFit.XErrorSize(0) );
            model_pdf_deco_relaxed.plotOn(mplot_deco,RooFit.Name("Nominal MC"),RooFit.LineColor(kBlack))
            rrv_number_dataset = RooRealVar("rrv_number_dataset","rrv_number_dataset",rdataset_relaxed.sumEntries());
            rrv_number_dataset.setError(0.); ## only shape uncertainty
            draw_error_band(rdataset_relaxed, model_pdf_relaxed,rrv_number_dataset,rfresult_pdf_relaxed,mplot_deco,self.color_palet["Uncertainty"],"F"); ## draw the error band with the area
           
            if self.workspace4fit_.pdf("model%smassvbf_jes_up%s_%s_mlvj_relaxed"%(label,in_range,self.channel)) :
               self.workspace4fit_.pdf("model%smassvbf_jes_up%s_%s_mlvj_relaxed"%(label,in_range,self.channel)).plotOn(mplot_deco,RooFit.Name("jes_up"), RooFit.LineColor(kRed));

            if self.workspace4fit_.pdf("model%smassvbf_jes_dn%s_%s_mlvj_relaxed"%(label,in_range,self.channel)) :
               self.workspace4fit_.pdf("model%smassvbf_jes_dn%s_%s_mlvj_relaxed"%(label,in_range,self.channel)).plotOn(mplot_deco,RooFit.Name("jes_dn"), RooFit.LineColor(kBlue));

            if self.workspace4fit_.pdf("model%smassvbf_jer%s_%s_mlvj_relaxed"%(label,in_range,self.channel)) :
               self.workspace4fit_.pdf("model%smassvbf_jer%s_%s_mlvj_relaxed"%(label,in_range,self.channel)).plotOn(mplot_deco,RooFit.Name("jer"), RooFit.LineColor(kAzure+1));

            if self.workspace4fit_.pdf("model%smassvbf_jer_up%s_%s_mlvj_relaxed"%(label,in_range,self.channel)) :
               self.workspace4fit_.pdf("model%smassvbf_jer_up%s_%s_mlvj_relaxed"%(label,in_range,self.channel)).plotOn(mplot_deco,RooFit.Name("jer_up"), RooFit.LineColor(kGreen+1));

            if self.workspace4fit_.pdf("model%smassvbf_jer_dn%s_%s_mlvj_relaxed"%(label,in_range,self.channel)) :
               self.workspace4fit_.pdf("model%smassvbf_jer_dn%s_%s_mlvj_relaxed"%(label,in_range,self.channel)).plotOn(mplot_deco,RooFit.Name("jer_dn"), RooFit.LineColor(6));

            if label == "_WJets0" and self.workspace4fit_.pdf("model_WJets01%s_%s_mlvj_relaxed"%(in_range,self.channel)):
                self.workspace4fit_.pdf("model_WJets01%s_%s_mlvj_relaxed"%(in_range,self.channel)).plotOn(mplot_sys,RooFit.Name("alt shape"), RooFit.LineColor(kOrange+1));


           self.leg = self.legend4Plot(mplot_deco,0,1,0., 0.06, 0.16, 0.);
           mplot_deco.addObject(self.leg);
           rdataset_relaxed.plotOn(mplot_deco, RooFit.Name("MC Events"), RooFit.MarkerSize(1.5), RooFit.DataError(RooAbsData.SumW2), RooFit.XErrorSize(0) );
           model_pdf_deco_relaxed.plotOn(mplot_deco,RooFit.Name("Nominal MC"),RooFit.LineColor(kBlack));
           mplot_deco.GetYaxis().SetRangeUser(1e-2,mplot_deco.GetMaximum()*1.2);

#           self.draw_canvas(mplot_deco,"plots_%s_%s_%s_%s_g1/other/"%(options.additioninformation, self.channel,self.PS_model,self.wtagger_label),in_file_name,"m_lvj_shape_relaxed"+label,0,1);
           self.draw_canvas_with_pull( mplot_deco, mplot_pull,parameters_list,"plots_%s_%s_%s_%s_g1/other/"%(options.additioninformation,self.channel,self.PS_model,self.wtagger_label),in_file_name,"m_lvj_shape_relaxed"+label+in_range+mlvj_model, show_constant_parameter, logy);

         par = parameters_list_relaxed.createIterator();
         par.Reset();
         param = par.Next()
         while (param):
             if TString(param.GetName()).Contains("number"):
                 param.setVal(param.getVal()*normalization);
                 param.setError(param.getError()*normalization);
                 param.Print();
             param=par.Next()

         result_param = rfresult_relaxed.floatParsFinal();

         for iresult in range(result_param.getSize()) :
          if TString(result_param.at(iresult).GetName()).Contains("number"):
           result_param.at(iresult).setVal(result_param.at(iresult).getVal()*normalization);
           result_param.at(iresult).setError(result_param.at(iresult).getError()*normalization);
                 
         ## draw the error band for an extend pdf
         rfresult_relaxed.Print();             

         mplot_same = rrv_mass_lvj.frame(RooFit.Title("M_{lvj"+in_range+"} fitted by "+mlvj_model), RooFit.Bins(int(rrv_mass_lvj.getBins()/self.narrow_factor)));
         rdataset.plotOn( mplot_same, RooFit.MarkerSize(1.5), RooFit.DataError(RooAbsData.SumW2), RooFit.XErrorSize(0) );

         ## set the name of the result of the fit and put it in the workspace
         rfresult_relaxed.SetName("rfresult_relaxed"+label+in_range+"_"+self.channel+"_mlvj")
         getattr(self.workspace4fit_,"import")(rfresult_relaxed)

         ## re-draw the dataset
         band_up = TGraph(); band_dn = TGraph();         
         band_up = mplot_relaxed.findObject("error_up");
         band_dn = mplot_relaxed.findObject("error_dn");
         
         for ipoint in range(0,band_up.GetN()) and range(0,band_dn.GetN()):
             x1 = ROOT.Double(0.) ; y1 = ROOT.Double(0.) ;
             band_up.GetPoint(ipoint,x1,y1);
             band_up.SetPoint(ipoint,x1,y1*normalization);
             x2 = ROOT.Double(0.) ; y2 = ROOT.Double(0.) ;
             band_dn.GetPoint(ipoint,x2,y2);
             band_dn.SetPoint(ipoint,x2,y2*normalization);
             
         mplot_same.addObject(band_up,"L");
         mplot_same.addObject(band_dn,"L"); 
        
         rdataset.plotOn(mplot_same,RooFit.MarkerSize(1.5),RooFit.DataError(RooAbsData.SumW2),RooFit.XErrorSize(0));
         ## draw the function
         model.plotOn(mplot_same, RooFit.LineColor(1));
         model_relaxed.plotOn(mplot_same);# remove RooFit.VLines() in order to get right pull in the 1st bin

         ## get the pull
         mplot_pull_same      = self.get_pull(rrv_mass_lvj,mplot_same);
         parameters_list_same = model_relaxed.getParameters(rdataset);
         mplot_same.GetYaxis().SetRangeUser(1e-5,mplot_same.GetMaximum()*1.2);

         ##CALCULATE CHI2
         datahist = rdataset.binnedClone(rdataset.GetName()+"_binnedClone",rdataset.GetName()+"_binnedClone")
         Nbin = int(rrv_mass_lvj.getBins()); 
         ChiSquare_same = model_relaxed.createChi2(datahist,RooFit.Extended(kTRUE),RooFit.SumW2Error(kTRUE));
         chi_over_ndf_same= ChiSquare_same.getVal()/(Nbin - nparameters_relaxed);

         ##Add Chisquare to mplot_pull
         cs3 = TLatex(0.75,0.8,"#chi^{2}/ndf = %0.2f "%(float(chi_over_ndf_same)));
         cs3.SetNDC();
         cs3.SetTextSize(0.12);
         cs3.AppendPad("same");
         mplot_pull_same.addObject(cs3)

         self.draw_canvas_with_pull( mplot_same, mplot_pull_same,parameters_list_same,"plots_%s_%s_%s_%s_g1/m_lvj_fitting_same/"%(options.additioninformation,self.channel,self.PS_model,self.wtagger_label),in_file_name,"m_lvj"+label+in_range+mlvj_model, show_constant_parameter, logy);

         ### Number of the event in the dataset and lumi scale factor --> set the proper number for bkg extraction or for signal region
         self.workspace4fit_.var("rrv_number"+label+in_range+"_"+self.channel+"_mlvj_relaxed").setVal(self.workspace4fit_.var("rrv_number"+label+in_range+"_"+self.channel+"_mlvj_relaxed").getVal()*self.workspace4fit_.var("rrv_scale_to_lumi"+label_origin+"_"+self.channel+in_range+"_mlvj").getVal())
         self.workspace4fit_.var("rrv_number"+label+in_range+"_"+self.channel+"_mlvj_relaxed").setError(self.workspace4fit_.var("rrv_number"+label+in_range+"_"+self.channel+"_mlvj").getError()*self.workspace4fit_.var("rrv_scale_to_lumi"+label_origin+"_"+self.channel+in_range+"_mlvj").getVal())

         self.workspace4fit_.var("rrv_number"+label+in_range+"_"+self.channel+"_mlvj_relaxed").Print();



    #### method to fit the WJets normalization inside the mj signal region -> and write the jets mass sys if available
    def fit_WJetsNorm(self, scaleJetMass = 0., relaxed = 0): # to get the normalization of WJets in signal_region

        print "############### Fit mj Normalization ##################"
        ## fit the two version of pdf for Wjets shape if available

        if relaxed == 0: regionvbf = ""  ;
        else : regionvbf = "_relaxed";

        self.fit_WJetsNormalization_in_Mj_signal_region("_WJets0","",regionvbf);
        self.fit_WJetsNormalization_in_Mj_signal_region("_WJets01","",regionvbf);
        rrv_WJets0  = self.workspace4fit_.var("rrv_number_WJets0_in_mj_signal_region_from_fitting_%s%s"%(self.channel,regionvbf)); ## nominal parametrization for Wjets
        rrv_WJets01 = self.workspace4fit_.var("rrv_number_WJets01_in_mj_signal_region_from_fitting_%s%s"%(self.channel,regionvbf)); ## alternate descrption

        rrv_WJets0.Print();
        rrv_WJets01.Print();

        total_uncertainty = TMath.Sqrt( TMath.Power(rrv_WJets0.getError(),2)+ TMath.Power(rrv_WJets01.getVal()-rrv_WJets0.getVal(),2) ); ## add in quadrature the difference
        rrv_WJets0.setError(total_uncertainty);
        rrv_WJets0.Print();
        print "Total Uncertainty in WJtes0 due to fit and shape: relaxed ",relaxed," uncertainty ",total_uncertainty/rrv_WJets0.getVal();

        if scaleJetMass :

         self.fit_WJetsNormalization_in_Mj_signal_region("_WJets0massvbf_jes_up","massvbf_jes_up",regionvbf); ## scale jet mass up   -> jes
         self.fit_WJetsNormalization_in_Mj_signal_region("_WJets0massvbf_jes_dn","massvbf_jes_dn",regionvbf); ## scale jet mass down -> jes        
         self.fit_WJetsNormalization_in_Mj_signal_region("_WJets0massvbf_jer"   ,"massvbf_jer",regionvbf); 
         self.fit_WJetsNormalization_in_Mj_signal_region("_WJets0massvbf_jer_up","massvbf_jer_up",regionvbf);         
         self.fit_WJetsNormalization_in_Mj_signal_region("_WJets0massvbf_jer_dn","massvbf_jer_dn",regionvbf);
          
         rrv_WJetsmassvbf_jes_up = self.workspace4fit_.var("rrv_number_WJets0massvbf_jes_up_in_mj_signal_region_from_fitting_%s%s"%(self.channel,regionvbf));
         rrv_WJetsmassvbf_jes_dn = self.workspace4fit_.var("rrv_number_WJets0massvbf_jes_dn_in_mj_signal_region_from_fitting_%s%s"%(self.channel,regionvbf));        
         rrv_WJetsmassvbf_jer    = self.workspace4fit_.var("rrv_number_WJets0massvbf_jer_in_mj_signal_region_from_fitting_%s%s"%(self.channel,regionvbf));
         rrv_WJetsmassvbf_jer_up = self.workspace4fit_.var("rrv_number_WJets0massvbf_jer_up_in_mj_signal_region_from_fitting_%s%s"%(self.channel,regionvbf));        
         rrv_WJetsmassvbf_jer_dn = self.workspace4fit_.var("rrv_number_WJets0massvbf_jer_dn_in_mj_signal_region_from_fitting_%s%s"%(self.channel,regionvbf));        

         rrv_WJetsmassvbf_jes_up.Print();
         rrv_WJetsmassvbf_jes_dn.Print();        
         rrv_WJetsmassvbf_jer.Print();        
         rrv_WJetsmassvbf_jer_up.Print();        
         rrv_WJetsmassvbf_jer_dn.Print();     

         #jet mass uncertainty on WJets normalization
         if(self.workspace4fit_.var("rrv_number_WJets0massvbf_jes_up_in_mj_signal_region_from_fitting_%s%s"%(self.channel,regionvbf)) and self.workspace4fit_.var("rrv_number_WJets0massvbf_jes_dn_in_mj_signal_region_from_fitting_%s%s"%(self.channel,regionvbf)) and self.workspace4fit_.var("rrv_number_WJets0massvbf_jer_in_mj_signal_region_from_fitting_%s%s"%(self.channel,regionvbf)) and self.workspace4fit_.var("rrv_number_WJets0massvbf_jer_up_in_mj_signal_region_from_fitting_%s%s"%(self.channel,regionvbf)) and self.workspace4fit_.var("rrv_number_WJets0massvbf_jer_dn_in_mj_signal_region_from_fitting_%s%s"%(self.channel,regionvbf))):    

            self.WJets_normalization_uncertainty_from_jet_scale = ((TMath.Abs(rrv_WJetsmassvbf_jes_up.getVal()-rrv_WJets0.getVal())+TMath.Abs(rrv_WJetsmassvbf_jes_dn.getVal()-rrv_WJets0.getVal() ) )/2.)/rrv_WJets0.getVal();         
            print "Total Uncertainty on WJtes0 due to jes: relaxed ",relaxed," uncertainty ",self.WJets_normalization_uncertainty_from_jet_scale;
            self.WJets_normalization_uncertainty_from_jet_res   = ((TMath.Abs(rrv_WJetsmassvbf_jer.getVal()-rrv_WJets0.getVal())+TMath.Abs(rrv_WJetsmassvbf_jer_up.getVal()-rrv_WJets0.getVal() )+TMath.Abs(rrv_WJetsmassvbf_jer_dn.getVal()-rrv_WJets0.getVal() ) )/3.)/rrv_WJets0.getVal();         
            print "Total Uncertainty on WJtes0 due to jes: relaxed ",relaxed," uncertainty ",self.WJets_normalization_uncertainty_from_jet_res;

         #jet mass uncertainty on sTop normalization
         rrv_STop                = self.workspace4fit_.var("rrv_number_dataset_signal_region_STop_%s_mj%s"%(self.channel,regionvbf))
         rrv_STopmassvbf_jes_up  = self.workspace4fit_.var("rrv_number_dataset_signal_region_STopmassvbf_jes_up_%s_mj%s"%(self.channel,regionvbf))
         rrv_STopmassvbf_jes_dn  = self.workspace4fit_.var("rrv_number_dataset_signal_region_STopmassvbf_jes_dn_%s_mj%s"%(self.channel,regionvbf))
         rrv_STopmassvbf_jer     = self.workspace4fit_.var("rrv_number_dataset_signal_region_STopmassvbf_jer_%s_mj%s"%(self.channel,regionvbf))
         rrv_STopmassvbf_jer_up  = self.workspace4fit_.var("rrv_number_dataset_signal_region_STopmassvbf_jer_up_%s_mj%s"%(self.channel,regionvbf))
         rrv_STopmassvbf_jer_dn  = self.workspace4fit_.var("rrv_number_dataset_signal_region_STopmassvbf_jer_dn_%s_mj%s"%(self.channel,regionvbf))
         
         rrv_STop.Print();
         rrv_STopmassvbf_jes_up.Print();
         rrv_STopmassvbf_jes_dn.Print();        
         rrv_STopmassvbf_jer.Print();        
         rrv_STopmassvbf_jer_up.Print();        
         rrv_STopmassvbf_jer_dn.Print();        

         #jet mass uncertainty on STop normalization
         if(self.workspace4fit_.var("rrv_number_dataset_signal_region_STopmassvbf_jes_up_%s_mj%s"%(self.channel,regionvbf)) and self.workspace4fit_.var("rrv_number_dataset_signal_region_STopmassvbf_jes_dn_%s_mj%s"%(self.channel,regionvbf)) and self.workspace4fit_.var("rrv_number_dataset_signal_region_STopmassvbf_jer_up_%s_mj%s"%(self.channel,regionvbf)) and self.workspace4fit_.var("rrv_number_dataset_signal_region_STopmassvbf_jer_dn_%s_mj%s"%(self.channel,regionvbf)) and self.workspace4fit_.var("rrv_number_dataset_signal_region_STopmassvbf_jer_%s_mj%s"%(self.channel,regionvbf))):    

            self.STop_normalization_uncertainty_from_jet_scale = ((TMath.Abs(rrv_STopmassvbf_jes_up.getVal()-rrv_STop.getVal())+TMath.Abs(rrv_STopmassvbf_jes_dn.getVal()-rrv_STop.getVal() ) )/2.)/rrv_STop.getVal();         
            print "Total Uncertainty on STop due to jes: relaxed ",relaxed," uncertainty ",self.STop_normalization_uncertainty_from_jet_scale;
            self.STop_normalization_uncertainty_from_jet_res   = ((TMath.Abs(rrv_STopmassvbf_jer.getVal()-rrv_STop.getVal())+TMath.Abs(rrv_STopmassvbf_jer_up.getVal()-rrv_STop.getVal() )+TMath.Abs(rrv_STopmassvbf_jer_dn.getVal()-rrv_STop.getVal() ) )/3.)/rrv_STop.getVal();         
            print "Total Uncertainty on STop due to jer: relaxed ",relaxed," uncertainty ",self.STop_normalization_uncertainty_from_jet_res;

         #jet mass uncertainty on TTbar normalization
         rrv_TTbar                 = self.workspace4fit_.var("rrv_number_dataset_signal_region_TTbar_%s_mj%s"%(self.channel,regionvbf))
         rrv_TTbarmassvbf_jes_up   = self.workspace4fit_.var("rrv_number_dataset_signal_region_TTbarmassvbf_jes_up_%s_mj%s"%(self.channel,regionvbf))
         rrv_TTbarmassvbf_jes_dn   = self.workspace4fit_.var("rrv_number_dataset_signal_region_TTbarmassvbf_jes_dn_%s_mj%s"%(self.channel,regionvbf))
         rrv_TTbarmassvbf_jer      = self.workspace4fit_.var("rrv_number_dataset_signal_region_TTbarmassvbf_jer_%s_mj%s"%(self.channel,regionvbf))
         rrv_TTbarmassvbf_jer_dn   = self.workspace4fit_.var("rrv_number_dataset_signal_region_TTbarmassvbf_jer_up_%s_mj%s"%(self.channel,regionvbf))
         rrv_TTbarmassvbf_jer_up   = self.workspace4fit_.var("rrv_number_dataset_signal_region_TTbarmassvbf_jer_dn_%s_mj%s"%(self.channel,regionvbf))

         rrv_TTbar.Print();
         rrv_TTbarmassvbf_jes_up.Print();
         rrv_TTbarmassvbf_jes_dn.Print();        
         rrv_TTbarmassvbf_jer.Print();        
         rrv_TTbarmassvbf_jer_up.Print();        
         rrv_TTbarmassvbf_jer_dn.Print();        


         #jet mass uncertainty on TTbar normalization
         if(self.workspace4fit_.var("rrv_number_dataset_signal_region_TTbarmassvbf_jes_up_%s_mj%s"%(self.channel,regionvbf)) and self.workspace4fit_.var("rrv_number_dataset_signal_region_TTbarmassvbf_jes_dn_%s_mj%s"%(self.channel,regionvbf)) and self.workspace4fit_.var("rrv_number_dataset_signal_region_TTbarmassvbf_jer_up_%s_mj%s"%(self.channel,regionvbf)) and self.workspace4fit_.var("rrv_number_dataset_signal_region_TTbarmassvbf_jer_dn_%s_mj%s"%(self.channel,regionvbf)) and self.workspace4fit_.var("rrv_number_dataset_signal_region_TTbarmassvbf_jer_%s_mj%s"%(self.channel,regionvbf))):    

            self.TTbar_normalization_uncertainty_from_jet_scale = ((TMath.Abs(rrv_TTbarmassvbf_jes_up.getVal()-rrv_TTbar.getVal())+TMath.Abs(rrv_TTbarmassvbf_jes_dn.getVal()-rrv_TTbar.getVal() ) )/2.)/rrv_TTbar.getVal();         
            print "Total Uncertainty on TTbar due to jes: relaxed ",relaxed," uncertainty ",self.TTbar_normalization_uncertainty_from_jet_scale;
            self.TTbar_normalization_uncertainty_from_jet_res   = ((TMath.Abs(rrv_TTbarmassvbf_jer.getVal()-rrv_TTbar.getVal())+TMath.Abs(rrv_TTbarmassvbf_jer_up.getVal()-rrv_TTbar.getVal() )+TMath.Abs(rrv_TTbarmassvbf_jer_dn.getVal()-rrv_TTbar.getVal() ) )/3.)/rrv_TTbar.getVal();         
            print "Total Uncertainty on TTbar due to jer: relaxed ",relaxed," uncertainty ",self.TTbar_normalization_uncertainty_from_jet_res;


         #jet mass uncertainty on VV normalization
         rrv_VV                 = self.workspace4fit_.var("rrv_number_dataset_signal_region_VV_%s_mj%s"%(self.channel,regionvbf))
         rrv_VVmassvbf_jes_up   = self.workspace4fit_.var("rrv_number_dataset_signal_region_VVmassvbf_jes_up_%s_mj%s"%(self.channel,regionvbf))
         rrv_VVmassvbf_jes_dn   = self.workspace4fit_.var("rrv_number_dataset_signal_region_VVmassvbf_jes_dn_%s_mj%s"%(self.channel,regionvbf))
         rrv_VVmassvbf_jer      = self.workspace4fit_.var("rrv_number_dataset_signal_region_VVmassvbf_jer_%s_mj%s"%(self.channel,regionvbf))
         rrv_VVmassvbf_jer_up   = self.workspace4fit_.var("rrv_number_dataset_signal_region_VVmassvbf_jer_up_%s_mj%s"%(self.channel,regionvbf))
         rrv_VVmassvbf_jer_dn   = self.workspace4fit_.var("rrv_number_dataset_signal_region_VVmassvbf_jer_dn_%s_mj%s"%(self.channel,regionvbf))

         rrv_VV.Print();
         rrv_VVmassvbf_jes_up.Print();
         rrv_VVmassvbf_jes_dn.Print();        
         rrv_VVmassvbf_jer_up.Print();
         rrv_VVmassvbf_jer_dn.Print();        
         rrv_VVmassvbf_jer.Print();        


         #jet mass uncertainty on VV normalization
         if(self.workspace4fit_.var("rrv_number_dataset_signal_region_VVmassvbf_jes_up_%s_mj%s"%(self.channel,regionvbf)) and self.workspace4fit_.var("rrv_number_dataset_signal_region_VVmassvbf_jes_dn_%s_mj%s"%(self.channel,regionvbf)) and self.workspace4fit_.var("rrv_number_dataset_signal_region_VVmassvbf_jer_up_%s_mj%s"%(self.channel,regionvbf)) and self.workspace4fit_.var("rrv_number_dataset_signal_region_VVmassvbf_jer_dn_%s_mj%s"%(self.channel,regionvbf)) and self.workspace4fit_.var("rrv_number_dataset_signal_region_VVmassvbf_jer_%s_mj%s"%(self.channel,regionvbf))):    

            self.VV_normalization_uncertainty_from_jet_scale = ((TMath.Abs(rrv_VVmassvbf_jes_up.getVal()-rrv_VV.getVal())+TMath.Abs(rrv_VVmassvbf_jes_dn.getVal()-rrv_VV.getVal() ) )/2.)/rrv_VV.getVal();         
            print "Total Uncertainty on VV due to jes: relaxed ",relaxed," uncertainty ",self.VV_normalization_uncertainty_from_jet_scale;
            self.VV_normalization_uncertainty_from_jet_res = ((TMath.Abs(rrv_VVmassvbf_jer_up.getVal()-rrv_VV.getVal())+TMath.Abs(rrv_VVmassvbf_jer_dn.getVal()-rrv_VV.getVal() )+TMath.Abs(rrv_VVmassvbf_jer.getVal()-rrv_VV.getVal() ) )/3.)/rrv_VV.getVal();         
            print "Total Uncertainty on VV due to jer: relaxed ",relaxed," uncertainty ",self.VV_normalization_uncertainty_from_jet_res;
 
         #jet mass uncertainty on WW_EWK normalization
         rrv_WW_EWK                = self.workspace4fit_.var("rrv_number_dataset_signal_region_WW_EWK_%s_mj%s"%(self.channel,regionvbf))
         rrv_WW_EWKmassvbf_jes_up  = self.workspace4fit_.var("rrv_number_dataset_signal_region_WW_EWKmassvbf_jes_up_%s_mj%s"%(self.channel,regionvbf))
         rrv_WW_EWKmassvbf_jes_dn  = self.workspace4fit_.var("rrv_number_dataset_signal_region_WW_EWKmassvbf_jes_dn_%s_mj%s"%(self.channel,regionvbf))
         rrv_WW_EWKmassvbf_jer     = self.workspace4fit_.var("rrv_number_dataset_signal_region_WW_EWKmassvbf_jer_%s_mj%s"%(self.channel,regionvbf))
         rrv_WW_EWKmassvbf_jer_up  = self.workspace4fit_.var("rrv_number_dataset_signal_region_WW_EWKmassvbf_jer_up_%s_mj%s"%(self.channel,regionvbf))
         rrv_WW_EWKmassvbf_jer_dn  = self.workspace4fit_.var("rrv_number_dataset_signal_region_WW_EWKmassvbf_jer_dn_%s_mj%s"%(self.channel,regionvbf))

         rrv_WW_EWK.Print();
         rrv_WW_EWKmassvbf_jes_up.Print();
         rrv_WW_EWKmassvbf_jes_dn.Print();
         rrv_WW_EWKmassvbf_jer_up.Print();
         rrv_WW_EWKmassvbf_jer_dn.Print();
         rrv_WW_EWKmassvbf_jer.Print();

         #jet mass uncertainty on WW_EWK normalization
         if(self.workspace4fit_.var("rrv_number_dataset_signal_region_WW_EWKmassvbf_jes_up_%s_mj%s"%(self.channel,regionvbf)) and self.workspace4fit_.var("rrv_number_dataset_signal_region_WW_EWKmassvbf_jes_dn_%s_mj%s"%(self.channel,regionvbf)) and self.workspace4fit_.var("rrv_number_dataset_signal_region_WW_EWKmassvbf_jer_up_%s_mj%s"%(self.channel,regionvbf)) and self.workspace4fit_.var("rrv_number_dataset_signal_region_WW_EWKmassvbf_jer_dn_%s_mj%s"%(self.channel,regionvbf)) and self.workspace4fit_.var("rrv_number_dataset_signal_region_WW_EWKmassvbf_jer_%s_mj%s"%(self.channel,regionvbf))):    

            self.WW_EWK_normalization_uncertainty_from_jet_scale = ((TMath.Abs(rrv_WW_EWKmassvbf_jes_up.getVal()-rrv_WW_EWK.getVal())+TMath.Abs(rrv_WW_EWKmassvbf_jes_dn.getVal()-rrv_WW_EWK.getVal() ) )/2.)/rrv_WW_EWK.getVal();         
            print "Total Uncertainty on WW_EWK due to jes: relaxed ",relaxed," uncertainty ",self.WW_EWK_normalization_uncertainty_from_jet_scale;
            self.WW_EWK_normalization_uncertainty_from_jet_res = ((TMath.Abs(rrv_WW_EWKmassvbf_jer_up.getVal()-rrv_WW_EWK.getVal())+TMath.Abs(rrv_WW_EWKmassvbf_jer_dn.getVal()-rrv_WW_EWK.getVal() )+TMath.Abs(rrv_WW_EWKmassvbf_jer.getVal()-rrv_WW_EWK.getVal() ) )/3.)/rrv_WW_EWK.getVal();         
            print "Total Uncertainty on WW_EWK due to jer: relaxed ",relaxed," uncertainty ",self.WW_EWK_normalization_uncertainty_from_jet_res;


         #jet mass uncertainty on ggH normalization
         rrv_ggH                  = self.workspace4fit_.var("rrv_number_dataset_signal_region_%s_%s_mj%s"%(self.higgs_sample,self.channel,regionvbf))
         rrv_ggHmassvbf_jes_up    = self.workspace4fit_.var("rrv_number_dataset_signal_region_%smassvbf_jes_up_%s_mj%s"%(self.higgs_sample,self.channel,regionvbf))
         rrv_ggHmassvbf_jes_dn    = self.workspace4fit_.var("rrv_number_dataset_signal_region_%smassvbf_jes_dn_%s_mj%s"%(self.higgs_sample,self.channel,regionvbf))
         rrv_ggHmassvbf_jer       = self.workspace4fit_.var("rrv_number_dataset_signal_region_%smassvbf_jer_%s_mj%s"%(self.higgs_sample,self.channel,regionvbf))
         rrv_ggHmassvbf_jer_up    = self.workspace4fit_.var("rrv_number_dataset_signal_region_%smassvbf_jer_up_%s_mj%s"%(self.higgs_sample,self.channel,regionvbf))
         rrv_ggHmassvbf_jer_dn    = self.workspace4fit_.var("rrv_number_dataset_signal_region_%smassvbf_jer_dn_%s_mj%s"%(self.higgs_sample,self.channel,regionvbf))

         rrv_ggH.Print();
         rrv_ggHmassvbf_jes_up.Print();
         rrv_ggHmassvbf_jes_dn.Print();        
         rrv_ggHmassvbf_jer.Print();        
         rrv_ggHmassvbf_jer_up.Print();        
         rrv_ggHmassvbf_jer_dn.Print();        

         #jet mass uncertainty on ggH normalization
         if(self.workspace4fit_.var("rrv_number_dataset_signal_region_%smassvbf_jes_up_%s_mj%s"%(self.higgs_sample,self.channel,regionvbf)) and self.workspace4fit_.var("rrv_number_dataset_signal_region_%smassvbf_jes_up_%s_mj%s"%(self.higgs_sample,self.channel,regionvbf)) and self.workspace4fit_.var("rrv_number_dataset_signal_region_%smassvbf_jer_up_%s_mj%s"%(self.higgs_sample,self.channel,regionvbf)) and self.workspace4fit_.var("rrv_number_dataset_signal_region_%smassvbf_jes_dn_%s_mj%s"%(self.higgs_sample,self.channel,regionvbf)) and self.workspace4fit_.var("rrv_number_dataset_signal_region_%smassvbf_jer_%s_mj%s"%(self.higgs_sample,self.channel,regionvbf))):    

            self.ggH_normalization_uncertainty_from_jet_scale = ((TMath.Abs(rrv_ggHmassvbf_jes_up.getVal()-rrv_ggH.getVal())+TMath.Abs(rrv_ggHmassvbf_jes_dn.getVal()-rrv_ggH.getVal() ) )/2.)/rrv_ggH.getVal();         
            print "Total Uncertainty on ggH due to jes: relaxed ",relaxed," uncertainty ",self.ggH_normalization_uncertainty_from_jet_scale;
            self.ggH_normalization_uncertainty_from_jet_res = ((TMath.Abs(rrv_ggHmassvbf_jer_up.getVal()-rrv_ggH.getVal())+TMath.Abs(rrv_ggHmassvbf_jer_dn.getVal()-rrv_ggH.getVal() )+TMath.Abs(rrv_ggHmassvbf_jer.getVal()-rrv_ggH.getVal() ) )/3.)/rrv_ggH.getVal();         
            print "Total Uncertainty on ggH due to jer: relaxed ",relaxed," uncertainty ",self.ggH_normalization_uncertainty_from_jet_res;


         #jet mass uncertainty on vbf normalizatio
         rrv_vbf                = self.workspace4fit_.var("rrv_number_dataset_signal_region_%s_%s_mj%s"%(self.vbfhiggs_sample,self.channel,regionvbf))
         rrv_vbfmassvbf_jes_up  = self.workspace4fit_.var("rrv_number_dataset_signal_region_%smassvbf_jes_up_%s_mj%s"%(self.vbfhiggs_sample,self.channel,regionvbf))
         rrv_vbfmassvbf_jes_dn  = self.workspace4fit_.var("rrv_number_dataset_signal_region_%smassvbf_jes_dn_%s_mj%s"%(self.vbfhiggs_sample,self.channel,regionvbf))
         rrv_vbfmassvbf_jer_up  = self.workspace4fit_.var("rrv_number_dataset_signal_region_%smassvbf_jer_up_%s_mj%s"%(self.vbfhiggs_sample,self.channel,regionvbf))
         rrv_vbfmassvbf_jer_dn  = self.workspace4fit_.var("rrv_number_dataset_signal_region_%smassvbf_jer_dn_%s_mj%s"%(self.vbfhiggs_sample,self.channel,regionvbf))
         rrv_vbfmassvbf_jer     = self.workspace4fit_.var("rrv_number_dataset_signal_region_%smassvbf_jer_%s_mj%s"%(self.vbfhiggs_sample,self.channel,regionvbf))

         rrv_vbf.Print();
         rrv_vbfmassvbf_jes_up.Print();
         rrv_vbfmassvbf_jes_dn.Print();        
         rrv_vbfmassvbf_jer_up.Print();        
         rrv_vbfmassvbf_jer_dn.Print();        
         rrv_vbfmassvbf_jer.Print();        

         #jet mass uncertainty on vbf normalization
         if(self.workspace4fit_.var("rrv_number_dataset_signal_region_%smassvbf_jes_up_%s_mj%s"%(self.vbfhiggs_sample,self.channel,regionvbf)) and self.workspace4fit_.var("rrv_number_dataset_signal_region_%smassvbf_jes_dn_%s_mj%s"%(self.vbfhiggs_sample,self.channel,regionvbf)) and self.workspace4fit_.var("rrv_number_dataset_signal_region_%smassvbf_jer_up_%s_mj%s"%(self.vbfhiggs_sample,self.channel,regionvbf)) and self.workspace4fit_.var("rrv_number_dataset_signal_region_%smassvbf_jer_dn_%s_mj%s"%(self.vbfhiggs_sample,self.channel,regionvbf)) and self.workspace4fit_.var("rrv_number_dataset_signal_region_%smassvbf_jer_%s_mj%s"%(self.vbfhiggs_sample,self.channel,regionvbf))):
             
            self.vbf_normalization_uncertainty_from_jet_scale = ((TMath.Abs(rrv_vbfmassvbf_jes_up.getVal()-rrv_vbf.getVal())+TMath.Abs(rrv_vbfmassvbf_jes_dn.getVal()-rrv_vbf.getVal() ) )/2.)/rrv_vbf.getVal();         
            print "Total Uncertainty on vbfH due to jes: relaxed ",relaxed," uncertainty ",self.vbf_normalization_uncertainty_from_jet_scale;
            self.vbf_normalization_uncertainty_from_jet_res   = ((TMath.Abs(rrv_vbfmassvbf_jer_up.getVal()-rrv_vbf.getVal())+TMath.Abs(rrv_vbfmassvbf_jer_dn.getVal()-rrv_vbf.getVal() )+TMath.Abs(rrv_vbfmassvbf_jer.getVal()-rrv_vbf.getVal() ) )/3.)/rrv_vbf.getVal();         
            print "Total Uncertainty on vbfH due to jer: relaxed ",relaxed," uncertainty ",self.vbf_normalization_uncertainty_from_jet_res;

    #### make the mj sideband fit on data ti get the Wjets normaliztion
    def fit_WJetsNormalization_in_Mj_signal_region(self,label,massscale="",relaxed = ""):

        print "############### Fit mj Normalization: ",label," ",massscale," relaxed ",relaxed," ##################"
	rrv_mass_j = self.workspace4fit_.var("rrv_mass_j")
        ## get real data in mj distribution --> mass up and down have only an effect on Wjets shape -> effect on the normalization -> evaluated in the MC and fit data
	rdataset_data_mj=self.workspace4fit_.data("rdataset_data_%s_mj"%self.channel)

	### Fix TTbar, VV and STop
        if relaxed == "":
         model_TTbar  = self.get_TTbar_mj_Model("_TTbar"+massscale);
         model_STop   = self.get_STop_mj_Model("_STop"+massscale);
         model_VV     = self.get_VV_mj_Model("_VV"+massscale);
         model_WW_EWK = self.get_WW_EWK_mj_Model("_WW_EWK"+massscale);
        else :
         model_TTbar  = self.get_TTbar_mj_Model("_TTbar"+massscale);
         model_STop   = self.get_STop_mj_Model("_STop"+massscale,1);
         model_VV     = self.get_VV_mj_Model("_VV"+massscale,1);
         model_WW_EWK = self.get_WW_EWK_mj_Model("_WW_EWK"+massscale,1);
            
        ## only two parameters are fix, offset and width while the exp is floating , otherwise if shape different User1 or ErfExp everything is flaoting
        model_WJets = self.get_WJets_mj_Model(label);

	## Total Pdf and fit only in sideband
        model_data = RooAddPdf("model_data%s_%s_mj%s"%(massscale,self.channel,relaxed),"model_data%s_%s_mj%s"%(massscale,self.channel,relaxed),RooArgList(model_WJets,model_VV,model_WW_EWK,model_TTbar,model_STop));
                
            
        rfresult = model_data.fitTo( rdataset_data_mj, RooFit.Save(1) , RooFit.Range("sb_lo,sb_hi") ,RooFit.Extended(kTRUE), RooFit.NumCPU(4) );
        rfresult = model_data.fitTo( rdataset_data_mj, RooFit.Save(1) , RooFit.Range("sb_lo,sb_hi") ,RooFit.Extended(kTRUE), RooFit.NumCPU(4), RooFit.Minimizer("Minuit2") );
        rfresult.Print();
	rfresult.covarianceMatrix().Print();
        getattr(self.workspace4fit_,"import")(model_data);

	## Total numver of event --> full propagation of error due to all the background sources coming from the fit
        rrv_number_data_mj = RooRealVar("rrv_number_data%s_%s_mj%s"%(massscale,self.channel,relaxed),"rrv_number_data%s_%s_mj%s"%(massscale,self.channel,relaxed),
                                         self.workspace4fit_.var("rrv_number_TTbar%s_%s_mj"%(massscale,self.channel)).getVal()+ ## TTbar
                                         self.workspace4fit_.var("rrv_number_STop%s_%s_mj%s"%(massscale,self.channel,relaxed)).getVal()+  ## STop
                                         self.workspace4fit_.var("rrv_number_VV%s_%s_mj%s"%(massscale,self.channel,relaxed)).getVal()+    ## VV
                                         self.workspace4fit_.var("rrv_number_WW_EWK%s_%s_mj%s"%(massscale,self.channel,relaxed)).getVal()+ ## WW_EWK
                                         self.workspace4fit_.var("rrv_number%s_%s_mj"%(label,self.channel)).getVal());  ## WJets

        rrv_number_data_mj.setError(TMath.Sqrt(self.workspace4fit_.var("rrv_number_TTbar%s_%s_mj"%(massscale,self.channel)).getError()*
                                               self.workspace4fit_.var("rrv_number_TTbar%s_%s_mj"%(massscale,self.channel)).getError()+
                                               self.workspace4fit_.var("rrv_number_STop%s_%s_mj%s"%(massscale,self.channel,relaxed)).getError()*
                                               self.workspace4fit_.var("rrv_number_STop%s_%s_mj%s"%(massscale,self.channel,relaxed)).getError()+
                                               self.workspace4fit_.var("rrv_number_VV%s_%s_mj%s"%(massscale,self.channel,relaxed)).getError()*
                                               self.workspace4fit_.var("rrv_number_VV%s_%s_mj%s"%(massscale,self.channel,relaxed)).getError()+
                                               self.workspace4fit_.var("rrv_number_WW_EWK%s_%s_mj%s"%(massscale,self.channel,relaxed)).getError()*
                                               self.workspace4fit_.var("rrv_number_WW_EWK%s_%s_mj%s"%(massscale,self.channel,relaxed)).getError()+       
                                               self.workspace4fit_.var("rrv_number%s_%s_mj"%(label,self.channel)).getError()*
                                               self.workspace4fit_.var("rrv_number%s_%s_mj"%(label,self.channel)).getError()));         
        getattr(self.workspace4fit_,"import")(rrv_number_data_mj);

        print self.workspace4fit_.var("rrv_number_TTbar%s_%s_mj"%(massscale,self.channel)).getVal();
        print self.workspace4fit_.var("rrv_number_STop%s_%s_mj%s"%(massscale,self.channel,relaxed)).getVal();
        print self.workspace4fit_.var("rrv_number_VV%s_%s_mj%s"%(massscale,self.channel,relaxed)).getVal();
        print self.workspace4fit_.var("rrv_number_WW_EWK%s_%s_mj%s"%(massscale,self.channel,relaxed)).getVal();
        print self.workspace4fit_.var("rrv_number%s_%s_mj"%(label,self.channel)).getVal();
        print self.workspace4fit_.var("rrv_number_data%s_%s_mj%s"%(massscale,self.channel,relaxed)).getVal();

        ## draw the plot for the default WJets Shape
        if TString(label).Contains("_WJets0"):

            ## make the final plot
            mplot = rrv_mass_j.frame(RooFit.Title(""), RooFit.Bins(int(rrv_mass_j.getBins()/self.narrow_factor)));
            rdataset_data_mj.plotOn(mplot, RooFit.Name("data_invisible"), RooFit.MarkerSize(1.5),RooFit.DataError(RooAbsData.SumW2), RooFit.XErrorSize(0));
            ## plot solid style
            model_data.plotOn(mplot,RooFit.Name("WW_EWK"), RooFit.Components("model%s_%s_mj,model_STop%s_%s_mj%s,model_TTbar%s_%s_mj,model_VV%s_%s_mj%s,model_WW_EWK%s_%s_mj%s"%(label,self.channel,massscale,self.channel,relaxed,massscale,self.channel,massscale,self.channel,relaxed,massscale,self.channel,relaxed)),RooFit.DrawOption("F"), RooFit.FillColor(self.color_palet["WW_EWK"]), RooFit.LineColor(kBlack),RooFit.NormRange("sb_lo,sb_hi"), RooFit.VLines());
            
            model_data.plotOn(mplot,RooFit.Name("VV"), RooFit.Components("model%s_%s_mj,model_STop%s_%s_mj%s,model_TTbar%s_%s_mj,model_VV%s_%s_mj%s"%(label,self.channel,massscale,self.channel,relaxed,massscale,self.channel,massscale,self.channel,relaxed)),RooFit.DrawOption("F"), RooFit.FillColor(self.color_palet["VV"]), RooFit.LineColor(kBlack),RooFit.NormRange("sb_lo,sb_hi"), RooFit.VLines());

            model_data.plotOn(mplot,RooFit.Name("TTbar"), RooFit.Components("model%s_%s_mj,model_STop%s_%s_mj%s,model_TTbar%s_%s_mj"%(label,self.channel,massscale,self.channel,relaxed,massscale,self.channel)),RooFit.DrawOption("F"), RooFit.FillColor(self.color_palet["TTbar"]), RooFit.LineColor(kBlack),RooFit.NormRange("sb_lo,sb_hi"), RooFit.VLines());

            model_data.plotOn(mplot,RooFit.Name("STop"), RooFit.Components("model%s_%s_mj,model_STop%s_%s_mj%s"%(label,self.channel,massscale,self.channel,relaxed)),RooFit.DrawOption("F"), RooFit.FillColor(self.color_palet["STop"]), RooFit.LineColor(kBlack),RooFit.NormRange("sb_lo,sb_hi"), RooFit.VLines());

            model_data.plotOn(mplot,RooFit.Name("WJets"), RooFit.Components("model%s_%s_mj"%(label,self.channel)),RooFit.DrawOption("F"), RooFit.FillColor(self.color_palet["WJets"]), RooFit.LineColor(kBlack),RooFit.NormRange("sb_lo,sb_hi"), RooFit.VLines());

            ## plot "dashed" style area
            model_data.plotOn(mplot,RooFit.Name("WW_EWK_invisible"), RooFit.Components("model%s_%s_mj,model_STop%s_%s_mj%s,model_TTbar%s_%s_mj,model_VV%s_%s_mj%s,model_WW_EWK%s_%s_mj%s"%(label,self.channel,massscale,self.channel,relaxed,massscale,self.channel,massscale,self.channel,relaxed,massscale,self.channel,relaxed)),RooFit.DrawOption("F"), RooFit.FillColor(self.color_palet["WW_EWK"]), RooFit.LineColor(kBlack),RooFit.FillStyle(3003),RooFit.Range(rrv_mass_j.getMin(),rrv_mass_j.getMax()),RooFit.NormRange("sb_lo,sb_hi"), RooFit.VLines());

            model_data.plotOn(mplot,RooFit.Name("VV_invisible"), RooFit.Components("model%s_%s_mj,model_STop%s_%s_mj%s,model_TTbar%s_%s_mj,model_VV%s_%s_mj%s"%(label,self.channel,massscale,self.channel,relaxed,massscale,self.channel,massscale,self.channel,relaxed)),RooFit.DrawOption("F"), RooFit.FillColor(self.color_palet["VV"]), RooFit.LineColor(kBlack),RooFit.FillStyle(3003),RooFit.Range(rrv_mass_j.getMin(),rrv_mass_j.getMax()),RooFit.NormRange("sb_lo,sb_hi"), RooFit.VLines());

            model_data.plotOn(mplot,RooFit.Name("TTbar_invisible"), RooFit.Components("model%s_%s_mj,model_STop%s_%s_mj%s,model_TTbar%s_%s_mj"%(label,self.channel,massscale,self.channel,relaxed,massscale,self.channel)),RooFit.DrawOption("F"), RooFit.FillColor(self.color_palet["TTbar"]), RooFit.LineColor(kBlack),RooFit.FillStyle(3003),RooFit.Range(rrv_mass_j.getMin(),rrv_mass_j.getMax()),RooFit.NormRange("sb_lo,sb_hi"), RooFit.VLines());

            model_data.plotOn(mplot,RooFit.Name("STop_invisible"), RooFit.Components("model%s_%s_mj,model_STop%s_%s_mj%s"%(label,self.channel,massscale,self.channel,relaxed)),RooFit.DrawOption("F"), RooFit.FillColor(self.color_palet["STop"]), RooFit.LineColor(kBlack),RooFit.FillStyle(3003),RooFit.Range(rrv_mass_j.getMin(),rrv_mass_j.getMax()),RooFit.NormRange("sb_lo,sb_hi"), RooFit.VLines());
            model_data.plotOn(mplot,RooFit.Name("WJets_invisible"), RooFit.Components("model%s_%s_mj"%(label,self.channel)),RooFit.DrawOption("F"), RooFit.FillColor(self.color_palet["WJets"]),RooFit.FillStyle(3003),RooFit.Range(rrv_mass_j.getMin(),rrv_mass_j.getMax()), RooFit.LineColor(kBlack),RooFit.NormRange("sb_lo,sb_hi"), RooFit.VLines());

            ### solid line
            model_data.plotOn( mplot,RooFit.Name("_invisible"), RooFit.Components("model%s_%s_mj"%(label,self.channel)), RooFit.LineColor(kBlack), RooFit.LineWidth(2) ,RooFit.NormRange("sb_lo,sb_hi"), RooFit.VLines());

            model_data.plotOn( mplot,RooFit.Name("_invisible"), RooFit.Components("model%s_%s_mj,model_STop%s_%s_mj%s"%(label,self.channel,massscale,self.channel,relaxed)), RooFit.LineColor(kBlack), RooFit.LineWidth(2),RooFit.NormRange("sb_lo,sb_hi"), RooFit.VLines());

            model_data.plotOn( mplot,RooFit.Name("_invisible"), RooFit.Components("model%s_%s_mj,model_STop%s_%s_mj%s,model_TTbar%s_%s_mj"%(label,self.channel,massscale,self.channel,relaxed,massscale,self.channel)), RooFit.LineColor(kBlack), RooFit.LineWidth(2) ,RooFit.NormRange("sb_lo,sb_hi"), RooFit.VLines());

            model_data.plotOn( mplot,RooFit.Name("_invisible"), RooFit.Components("model%s_%s_mj,model_STop%s_%s_mj%s,model_TTbar%s_%s_mj,model_VV%s_%s_mj%s"%(label,self.channel,massscale,self.channel,relaxed,massscale,self.channel,massscale,self.channel,relaxed)),RooFit.LineColor(kBlack), RooFit.LineWidth(2) ,RooFit.NormRange("sb_lo,sb_hi"), RooFit.VLines());

            model_data.plotOn( mplot,RooFit.Name("_invisible"), RooFit.Components("model%s_%s_mj,model_STop%s_%s_mj%s,model_TTbar%s_%s_mj,model_VV%s_%s_mj%s,model_WW_EWK%s_%s_mj%s"%(label,self.channel,massscale,self.channel,relaxed,massscale,self.channel,massscale,self.channel,relaxed,massscale,self.channel,relaxed)),RooFit.LineColor(kBlack), RooFit.LineWidth(2) ,RooFit.NormRange("sb_lo,sb_hi"), RooFit.VLines());            

            ### dash line
            model_data.plotOn( mplot,RooFit.Name("_invisible"), RooFit.Components("model%s_%s_mj"%(label,self.channel)), RooFit.LineColor(kBlack), RooFit.LineWidth(2), RooFit.Range(rrv_mass_j.getMin(),rrv_mass_j.getMax()),RooFit.LineStyle(kDashed) ,RooFit.NormRange("sb_lo,sb_hi"), RooFit.VLines());

            model_data.plotOn( mplot,RooFit.Name("_invisible"), RooFit.Components("model%s_%s_mj,model_STop%s_%s_mj%s"%(label,self.channel,massscale,self.channel,relaxed)), RooFit.LineColor(kBlack), RooFit.LineWidth(2), RooFit.Range(rrv_mass_j.getMin(),rrv_mass_j.getMax()),RooFit.LineStyle(kDashed) ,RooFit.NormRange("sb_lo,sb_hi"), RooFit.VLines());

            model_data.plotOn( mplot,RooFit.Name("_invisible"), RooFit.Components("model%s_%s_mj,model_STop%s_%s_mj%s,model_TTbar%s_%s_mj"%(label,self.channel,massscale,self.channel,relaxed,massscale,self.channel)), RooFit.LineColor(kBlack), RooFit.LineWidth(2), RooFit.Range(rrv_mass_j.getMin(),rrv_mass_j.getMax()),RooFit.LineStyle(kDashed) ,RooFit.NormRange("sb_lo,sb_hi"), RooFit.VLines());

            model_data.plotOn( mplot,RooFit.Name("_invisible"), RooFit.Components("model%s_%s_mj,model_STop%s_%s_mj%s,model_TTbar%s_%s_mj,model_VV%s_%s_mj%s"%(label,self.channel,massscale,self.channel,relaxed,massscale,self.channel,massscale,self.channel,relaxed)),RooFit.LineColor(kBlack), RooFit.LineWidth(2), RooFit.Range(rrv_mass_j.getMin(),rrv_mass_j.getMax()),RooFit.LineStyle(kDashed) ,RooFit.NormRange("sb_lo,sb_hi"), RooFit.VLines());

            model_data.plotOn( mplot,RooFit.Name("_invisible"), RooFit.Components("model%s_%s_mj,model_STop%s_%s_mj%s,model_TTbar%s_%s_mj,model_VV%s_%s_mj%s,model_WW_EWK%s_%s_mj%s"%(label,self.channel,massscale,self.channel,relaxed,massscale,self.channel,massscale,self.channel,relaxed,massscale,self.channel,relaxed)),RooFit.LineColor(kBlack), RooFit.LineWidth(2), RooFit.Range(rrv_mass_j.getMin(),rrv_mass_j.getMax()),RooFit.LineStyle(kDashed) ,RooFit.NormRange("sb_lo,sb_hi"));

            ### draw the error band using the sum of all the entries component MC + fit and the total error == Normalization for the fixed MC, shape + normalization for W+jets
            draw_error_band(rdataset_data_mj, model_data, rrv_number_data_mj,rfresult,mplot,self.color_palet["Uncertainty"],"F");
            rdataset_data_mj.plotOn(mplot, RooFit.Name("data"), RooFit.MarkerSize(1.5), RooFit.DataError(RooAbsData.SumW2), RooFit.XErrorSize(0) );
                
            ### Get the pull and plot it
            mplot_pull = self.get_pull(rrv_mass_j,mplot);

            ### signal window zone with vertical lines
            lowerLine = TLine(self.mj_signal_min,0.,self.mj_signal_min,mplot.GetMaximum()*0.9); lowerLine.SetLineWidth(2); lowerLine.SetLineColor(kGray+2); lowerLine.SetLineStyle(9);
            upperLine = TLine(self.mj_signal_max,0.,self.mj_signal_max,mplot.GetMaximum()*0.9); upperLine.SetLineWidth(2); upperLine.SetLineColor(kGray+2); upperLine.SetLineStyle(9);
            mplot.addObject(lowerLine);
            mplot.addObject(upperLine);

            ### legend of the plot
            self.leg = self.legend4Plot(mplot,0,1, -0.2, 0.07, 0.04, 0.);
            mplot.addObject(self.leg);
            mplot.GetYaxis().SetRangeUser(1e-2,mplot.GetMaximum()*1.5);

            ## CALCULATE CHI2
            datahist = rdataset_data_mj.binnedClone(rdataset_data_mj.GetName()+"_binnedClone",rdataset_data_mj.GetName()+"_binnedClone")
            Nbin = int(rrv_mass_j.getBins()); 
            rresult_param = rfresult.floatParsFinal();        
            nparameters =  rresult_param.getSize()                                         
            ChiSquare = model_data.createChi2(datahist,RooFit.Extended(kTRUE),RooFit.DataError(RooAbsData.Poisson));
            chi_over_ndf= ChiSquare.getVal()/(Nbin - nparameters);

            ## Add Chisquare to mplot_pull
            cs = TLatex(0.75,0.8,"#chi^{2}/ndf = %0.2f "%(float(chi_over_ndf)));
            cs.SetNDC();
            cs.SetTextSize(0.12);
            cs.AppendPad("same");
            mplot_pull.addObject(cs)

            parameters_list = model_data.getParameters(rdataset_data_mj);
            if relaxed == "":
             self.draw_canvas_with_pull( mplot, mplot_pull,parameters_list,"plots_%s_%s_%s_%s_g1/m_j_fitting_wtaggercut%s/"%(options.additioninformation, self.channel,self.PS_model,self.wtagger_label, self.wtagger_label), "m_j_sideband%s"%(label),"",1)
            else:
             self.draw_canvas_with_pull( mplot, mplot_pull,parameters_list,"plots_%s_%s_%s_%s_g1/m_j_fitting_wtaggercut%s_relaxed/"%(options.additioninformation, self.channel,self.PS_model,self.wtagger_label, self.wtagger_label), "m_j_sideband%s"%(label),"",1)
                
            ### call the function for getting the normalizatio in signal region for data, TTbar, STop, VV and W+jets = label -> store in a output txt file
            if relaxed == "":
               self.get_mj_normalization_insignalregion("_data");
               self.get_mj_normalization_insignalregion("_TTbar");
               self.get_mj_normalization_insignalregion("_STop");
               self.get_mj_normalization_insignalregion("_VV");
               self.get_mj_normalization_insignalregion("_WW_EWK");
               self.get_mj_normalization_insignalregion(label);
            else:
               self.get_mj_normalization_insignalregion("_data");
               self.get_mj_normalization_insignalregion("_TTbar");
               self.get_mj_normalization_insignalregion("_STop",1);
               self.get_mj_normalization_insignalregion("_VV",1);
               self.get_mj_normalization_insignalregion("_WW_EWK",1);
               self.get_mj_normalization_insignalregion(label);
                                                                                                                                                                                
        #### to calculate the WJets's normalization and error in M_J signal_region. The error must contain the shape error: model_WJets have new parameters fitting data
        fullInt   = model_WJets.createIntegral(RooArgSet(rrv_mass_j),RooArgSet(rrv_mass_j) );
        signalInt = model_WJets.createIntegral(RooArgSet(rrv_mass_j),RooArgSet(rrv_mass_j),("signal_region"));
        fullInt_val = fullInt.getVal();
        signalInt_val = signalInt.getVal()/fullInt_val;
        ## take the value from the fit (normalization) and multiply it from the ratio of the integrals
        rrv_number_WJets_in_mj_signal_region_from_fitting = RooRealVar("rrv_number%s_in_mj_signal_region_from_fitting_%s%s"%(label,self.channel,relaxed),"rrv_number%s_in_mj_signal_region_from_fitting_%s%s"%(label,self.channel,relaxed),self.workspace4fit_.var("rrv_number%s_%s_mj"%(label,self.channel)).getVal()*signalInt_val);

        #### Error on the normalization --> from a dedicated function taking into account shape uncertainty on the parameters that are floating in the fit)
        rrv_number_WJets_in_mj_signal_region_from_fitting.setError( Calc_error_extendPdf(rdataset_data_mj, model_WJets, rfresult,"signal_region") );
        print "########## error on the normaliztion due to shape + norm = %s"%(rrv_number_WJets_in_mj_signal_region_from_fitting.getError());
        getattr(self.workspace4fit_,"import")(rrv_number_WJets_in_mj_signal_region_from_fitting);
        rrv_number_WJets_in_mj_signal_region_from_fitting.Print();


    ##### Counting of the events of each component in the signal region taking the lavel for the model
    def get_mj_normalization_insignalregion(self, label, relaxed = 0):
        print "################## get mj normalization ",label," ################## ";
        rrv_mass_j = self.workspace4fit_.var("rrv_mass_j");
        if relaxed == 0 :
         model = self.workspace4fit_.pdf("model"+label+"_"+self.channel+"_mj");
        else :
         model = self.workspace4fit_.pdf("model"+label+"_"+self.channel+"_mj_relaxed");
                                  
	fullInt   = model.createIntegral(RooArgSet(rrv_mass_j),RooArgSet(rrv_mass_j) );
	sb_loInt  = model.createIntegral(RooArgSet(rrv_mass_j),RooArgSet(rrv_mass_j),("sb_lo"));
        signalInt = model.createIntegral(RooArgSet(rrv_mass_j),RooArgSet(rrv_mass_j),("signal_region"));
        sb_hiInt  = model.createIntegral(RooArgSet(rrv_mass_j),RooArgSet(rrv_mass_j),("sb_hi"));

	fullInt_val   = fullInt.getVal()
        sb_loInt_val  = sb_loInt.getVal()/fullInt_val
        sb_hiInt_val  = sb_hiInt.getVal()/fullInt_val
        signalInt_val = signalInt.getVal()/fullInt_val

        print "########### Events Number in MC Dataset: #############"
        if relaxed == 0:    
         self.workspace4fit_.var("rrv_number_dataset_sb_lo"+label+"_"+self.channel+"_mj").Print();
         self.workspace4fit_.var("rrv_number_dataset_signal_region"+label+"_"+self.channel+"_mj").Print();
         self.workspace4fit_.var("rrv_number_dataset_sb_hi"+label+"_"+self.channel+"_mj").Print();
        else:
         self.workspace4fit_.var("rrv_number_dataset_sb_lo"+label+"_"+self.channel+"_mj_relaxed").Print();
         self.workspace4fit_.var("rrv_number_dataset_signal_region"+label+"_"+self.channel+"_mj_relaxed").Print();
         self.workspace4fit_.var("rrv_number_dataset_sb_hi"+label+"_"+self.channel+"_mj_relaxed").Print();
            
        print "########### Events Number get from fit: ##############"
        if relaxed == 0:
         rrv_tmp = self.workspace4fit_.var("rrv_number"+label+"_"+self.channel+"_mj");
         rrv_tmp.Print();
        else:
         rrv_tmp = self.workspace4fit_.var("rrv_number"+label+"_"+self.channel+"_mj_relaxed");
         rrv_tmp.Print();

        print "Events Number in sideband_low :%s"%(rrv_tmp.getVal()*sb_loInt_val)
        print "Events Number in Signal Region:%s"%(rrv_tmp.getVal()*signalInt_val)
        print "Events Number in sideband_high:%s"%(rrv_tmp.getVal()*sb_hiInt_val)
        print "Total Number in sidebands :%s"%(rrv_tmp.getVal()*(sb_loInt_val+sb_hiInt_val) )
        print "Ratio signal_region/sidebands :%s"%(signalInt_val/(sb_loInt_val+sb_hiInt_val) )

        ##### Save numbers in the output text file
        self.file_out.write( "\n%s++++++++++++++++++++++++++++++++++++"%(label) );
        self.file_out.write( "\nEvents Number in sideband_low from dataset:%s"%(self.workspace4fit_.var("rrv_number_dataset_sb_lo"+label+"_"+self.channel+"_mj").getVal() ) );
        self.file_out.write( "\nEvents Number in Signal Region from dataset:%s"%(self.workspace4fit_.var("rrv_number_dataset_signal_region"+label+"_"+self.channel+"_mj").getVal() ) );
        self.file_out.write( "\nEvents Number in sideband_high from dataset:%s"%(self.workspace4fit_.var("rrv_number_dataset_sb_hi"+label+"_"+self.channel+"_mj").getVal() ) );
        self.file_out.write( "\nTotal Number in sidebands from dataset:%s"%(self.workspace4fit_.var("rrv_number_dataset_sb_lo"+label+"_"+self.channel+"_mj").getVal()+ self.workspace4fit_.var("rrv_number_dataset_sb_hi"+label+"_"+self.channel+"_mj").getVal() ) );
        self.file_out.write( "\nRatio signal_region/sidebands from dataset:%s"%(self.workspace4fit_.var("rrv_number_dataset_signal_region"+label+"_"+self.channel+"_mj").getVal()/(self.workspace4fit_.var("rrv_number_dataset_sb_lo"+label+"_"+self.channel+"_mj").getVal()+ self.workspace4fit_.var("rrv_number_dataset_sb_hi"+label+"_"+self.channel+"_mj").getVal()) ) );


        self.file_out.write( "\nEvents Number in sideband_low from fitting:%s"%(rrv_tmp.getVal()*sb_loInt_val) );
        self.file_out.write( "\nEvents Number in Signal Region from fitting:%s"%(rrv_tmp.getVal()*signalInt_val) );
        self.file_out.write( "\nEvents Number in sideband_high from fitting:%s"%(rrv_tmp.getVal()*sb_hiInt_val) );
        self.file_out.write( "\nTotal Number in sidebands from fitting:%s"%(rrv_tmp.getVal()*(sb_loInt_val+sb_hiInt_val) ) );
        self.file_out.write( "\nRatio signal_region/sidebands from fitting:%s"%(signalInt_val/(sb_loInt_val+sb_hiInt_val) ) );

    ##### Method to fit data mlvj shape in the sideband -> first step for the background extraction of the shape
    def fit_mlvj_in_Mj_sideband(self, label, mlvj_region, mlvj_model,logy = 0,relaxed = 0):

        if relaxed == 0: regionvbf = "";
        else: regionvbf = "_relaxed";

        print "############### Fit mlvj in mj sideband: ",label," ",mlvj_region,"  ",mlvj_model," ##################"
        rrv_mass_j   = self.workspace4fit_.var("rrv_mass_j");
        rrv_mass_lvj = self.workspace4fit_.var("rrv_mass_lvj");
        rdataset_data_mlvj = self.workspace4fit_.data("rdataset_data%s_%s_mlvj%s"%(mlvj_region,self.channel,regionvbf));
        rdataset_data_mlvj.Print();
          
	## get the minor component shapes in the sb low
        model_VV_backgrounds      = self.get_VV_mlvj_Model("_sb_lo",relaxed);
        model_WW_EWK_backgrounds  = self.get_WW_EWK_mlvj_Model("_sb_lo",relaxed);
        model_TTbar_backgrounds   = self.get_TTbar_mlvj_Model("_sb_lo",relaxed);
        model_STop_backgrounds    = self.get_STop_mlvj_Model("_sb_lo",relaxed);

        if relaxed == 0:

          number_VV_sb_lo_mlvj     = self.workspace4fit_.var("rrv_number_VV_sb_lo_%s_mlvj"%(self.channel))
          number_WW_EWK_sb_lo_mlvj = self.workspace4fit_.var("rrv_number_WW_EWK_sb_lo_%s_mlvj"%(self.channel))        
          number_TTbar_sb_lo_mlvj  = self.workspace4fit_.var("rrv_number_TTbar_sb_lo_%s_mlvj"%(self.channel))
          number_STop_sb_lo_mlvj   = self.workspace4fit_.var("rrv_number_STop_sb_lo_%s_mlvj"%(self.channel))

          self.workspace4fit_.var("rrv_number_TTbar_sb_lo_%s_mlvj"%(self.channel)).Print();
          self.workspace4fit_.var("rrv_number_STop_sb_lo_%s_mlvj"%(self.channel)).Print();
          self.workspace4fit_.var("rrv_number_VV_sb_lo_%s_mlvj"%(self.channel)).Print();
          self.workspace4fit_.var("rrv_number_WW_EWK_sb_lo_%s_mlvj"%(self.channel)).Print();        

        else:
            
          number_VV_sb_lo_mlvj      = self.workspace4fit_.var("rrv_number_VV_sb_lo_%s_mlvj_relaxed"%(self.channel)).getVal()*self.workspace4fit_.var("rrv_vbf_cut_sb_lo_VV_"+self.channel).getVal();
          number_WW_EWK_sb_lo_mlvj  = self.workspace4fit_.var("rrv_number_WW_EWK_sb_lo_%s_mlvj_relaxed"%(self.channel)).getVal()*self.workspace4fit_.var("rrv_vbf_cut_sb_lo_WW_EWK_"+self.channel).getVal(); 
          number_TTbar_sb_lo_mlvj   = self.workspace4fit_.var("rrv_number_TTbar_sb_lo_%s_mlvj_relaxed"%(self.channel)).getVal()*self.workspace4fit_.var("rrv_vbf_cut_sb_lo_TTbar_"+self.channel).getVal();
          number_STop_sb_lo_mlvj    = self.workspace4fit_.var("rrv_number_STop_sb_lo_%s_mlvj_relaxed"%(self.channel)).getVal()*self.workspace4fit_.var("rrv_vbf_cut_sb_lo_STop_"+self.channel).getVal();
          
          self.workspace4fit_.var("rrv_number_TTbar_sb_lo_%s_mlvj_relaxed"%(self.channel)).Print();
          self.workspace4fit_.var("rrv_number_STop_sb_lo_%s_mlvj_relaxed"%(self.channel)).Print();
          self.workspace4fit_.var("rrv_number_VV_sb_lo_%s_mlvj_relaxed"%(self.channel)).Print();
          self.workspace4fit_.var("rrv_number_WW_EWK_sb_lo_%s_mlvj_relaxed"%(self.channel)).Print();        
     

        ### Make the Pdf for the WJets
        model_pdf_WJets = self.make_Pdf("%s_sb_lo_from_fitting"%(label), mlvj_model,"_mlvj%s"%(regionvbf));
        model_pdf_WJets.Print();

        ### inititalize the value to what was fitted with the mc in the sideband        
        number_WJets_sb_lo = self.workspace4fit_.var("rrv_number%s_sb_lo_%s_mlvj%s"%(label,self.channel,regionvbf)).clone("rrv_number%s_sb_lo_from_fitting_%s_mlvj%s"%(label,self.channel,regionvbf));
#        number_WJets_sb_lo = RooRealVar("rrv_number%s_sb_lo_from_fitting_%s_mlvj%s"%(label,self.channel,regionvbf),"rrv_number%s_sb_lo_from_fitting_%s_mlvj%s"%(label,self.channel,regionvbf),number_TTbar_sb_lo_mlvj.getVal(),0.,1e7);

        model_WJets = RooExtendPdf("model%s_sb_lo_from_fitting_%s_mlvj%s"%(label,self.channel,regionvbf),"model%s_sb_lo_from_fitting_%s_mlvj%s"%(label,self.channel,regionvbf),model_pdf_WJets,number_WJets_sb_lo);
        number_WJets_sb_lo.Print();

        ## Add the other bkg component fixed to the total model
        model_data = RooAddPdf("model_data%s%s_mlvj%s"%(label,mlvj_region,regionvbf),"model_data%s%s_mlvj%s"%(label,mlvj_region,regionvbf),RooArgList(model_WJets,model_VV_backgrounds, model_TTbar_backgrounds, model_STop_backgrounds, model_WW_EWK_backgrounds));

        rfresult = model_data.fitTo( rdataset_data_mlvj, RooFit.Save(1) ,RooFit.Extended(kTRUE));
        rfresult = model_data.fitTo( rdataset_data_mlvj, RooFit.Save(1) ,RooFit.Extended(kTRUE), RooFit.Minimizer("Minuit2"));
        rfresult.Print();

        rfresult.covarianceMatrix().Print();
        getattr(self.workspace4fit_,"import")(model_data);

        model_WJets.Print();
        model_WJets.getParameters(rdataset_data_mlvj).Print("v");
        #self.workspace4fit_.pdf("model_pdf%s_sb_lo_%s_mlvj%s"%(label,self.channel,regionvbf)).getParameters(rdataset_data_mlvj).Print("v");

        ### data in the sideband plus error from fit
        rrv_number_data_sb_lo_mlvj = RooRealVar("rrv_number_data_sb_lo_%s_mlvj%s"%(self.channel,regionvbf),"rrv_number_data_sb_lo_%s_mlvj%s"%(self.channel,regionvbf),
                                                 self.workspace4fit_.var("rrv_number_TTbar_sb_lo_%s_mlvj%s"%(self.channel,regionvbf)).getVal()+
                                                 self.workspace4fit_.var("rrv_number_STop_sb_lo_%s_mlvj%s"%(self.channel,regionvbf)).getVal()+
                                                 self.workspace4fit_.var("rrv_number_VV_sb_lo_%s_mlvj%s"%(self.channel,regionvbf)).getVal()+
                                                 self.workspace4fit_.var("rrv_number_WW_EWK_sb_lo_%s_mlvj%s"%(self.channel,regionvbf)).getVal()+                 
                                                 self.workspace4fit_.var("rrv_number%s_sb_lo_from_fitting_%s_mlvj%s"%(label,self.channel,regionvbf)).getVal() );

        rrv_number_data_sb_lo_mlvj.setError( TMath.Sqrt(self.workspace4fit_.var("rrv_number%s_sb_lo_from_fitting_%s_mlvj%s"%(label,self.channel,regionvbf)).getError()*
                                                        self.workspace4fit_.var("rrv_number%s_sb_lo_from_fitting_%s_mlvj%s"%(label,self.channel,regionvbf)).getError()+
                                                        self.workspace4fit_.var("rrv_number_TTbar_sb_lo_%s_mlvj%s"%(self.channel,regionvbf)).getError()*
                                                        self.workspace4fit_.var("rrv_number_TTbar_sb_lo_%s_mlvj%s"%(self.channel,regionvbf)).getError()+
                                                        self.workspace4fit_.var("rrv_number_STop_sb_lo_%s_mlvj%s"%(self.channel,regionvbf)).getError()*
                                                        self.workspace4fit_.var("rrv_number_STop_sb_lo_%s_mlvj%s"%(self.channel,regionvbf)).getError()+
                                                        self.workspace4fit_.var("rrv_number_VV_sb_lo_%s_mlvj%s"%(self.channel,regionvbf)).getError()*
                                                        self.workspace4fit_.var("rrv_number_VV_sb_lo_%s_mlvj%s"%(self.channel,regionvbf)).getError()+
                                                        self.workspace4fit_.var("rrv_number_WW_EWK_sb_lo_%s_mlvj%s"%(self.channel,regionvbf)).getError()*
                                                        self.workspace4fit_.var("rrv_number_WW_EWK_sb_lo_%s_mlvj%s"%(self.channel,regionvbf)).getError()));        


        getattr(self.workspace4fit_,"import")(rrv_number_data_sb_lo_mlvj);

        ### plot for WJets default + default shape
        mplot = rrv_mass_lvj.frame(RooFit.Title("M_lvj fitted in M_j sideband "), RooFit.Bins(int(rrv_mass_lvj.getBins()/self.narrow_factor)));
        rdataset_data_mlvj.plotOn( mplot , RooFit.Invisible(), RooFit.MarkerSize(1.5), RooFit.DataError(RooAbsData.SumW2), RooFit.XErrorSize(0) );

        model_data.plotOn(mplot, RooFit.Components("model%s_sb_lo_from_fitting_%s_mlvj%s,model_TTbar_sb_lo_%s_mlvj%s,model_STop_sb_lo_%s_mlvj%s,model_VV_sb_lo_%s_mlvj%s,model_WW_EWK_sb_lo_%s_mlvj%s"%(label,self.channel,regionvbf,self.channel,regionvbf,self.channel,regionvbf,self.channel,regionvbf,self.channel,regionvbf)), RooFit.Name("WJets"),RooFit.DrawOption("F"), RooFit.FillColor(self.color_palet["WJets"]), RooFit.LineColor(kBlack), RooFit.VLines());

        model_data.plotOn(mplot, RooFit.Components("model_TTbar_sb_lo_%s_mlvj%s,model_STop_sb_lo_%s_mlvj%s,model_VV_sb_lo_%s_mlvj%s,model_WW_EWK_sb_lo_%s_mlvj%s"%(self.channel,regionvbf,self.channel,regionvbf,self.channel,regionvbf,self.channel,regionvbf)), RooFit.Name("WW_EWK"),RooFit.DrawOption("F"), RooFit.FillColor(self.color_palet["WW_EWK"]), RooFit.LineColor(kBlack), RooFit.VLines());

        model_data.plotOn(mplot, RooFit.Components("model_TTbar_sb_lo_%s_mlvj%s,model_STop_sb_lo_%s_mlvj%s,model_VV_sb_lo_%s_mlvj%s"%(self.channel,regionvbf,self.channel,regionvbf,self.channel,regionvbf)),RooFit.Name("VV"),RooFit.DrawOption("F"), RooFit.FillColor(self.color_palet["VV"]), RooFit.LineColor(kBlack), RooFit.VLines()) ;

        model_data.plotOn(mplot, RooFit.Components("model_TTbar_sb_lo_%s_mlvj%s,model_STop_sb_lo_%s_mlvj%s"%(self.channel,regionvbf,self.channel,regionvbf)), RooFit.Name("TTbar"),RooFit.DrawOption("F"), RooFit.FillColor(self.color_palet["TTbar"]), RooFit.LineColor(kBlack), RooFit.VLines());

        model_data.plotOn(mplot, RooFit.Components("model_STop_sb_lo_%s_mlvj%s"%(self.channel,regionvbf)), RooFit.Name("STop"), RooFit.DrawOption("F"), RooFit.FillColor(self.color_palet["STop"]), RooFit.LineColor(kBlack), RooFit.VLines());

        #solid line
        model_data.plotOn(mplot, RooFit.Components("model%s_sb_lo_from_fitting_%s_mlvj%s,model_TTbar_sb_lo_%s_mlvj%s,model_STop_sb_lo_%s_mlvj%s,model_VV_sb_lo_%s_mlvj%s,model_WW_EWK_sb_lo_%s_mlvj%s"%(label,self.channel,regionvbf,self.channel,regionvbf,self.channel,regionvbf,self.channel,regionvbf,self.channel,regionvbf)), RooFit.Name("WJets_line_invisible"), RooFit.LineColor(kBlack), RooFit.LineWidth(2), RooFit.VLines()) ;

        model_data.plotOn(mplot, RooFit.Components("model_TTbar_sb_lo_%s_mlvj%s,model_STop_sb_lo_%s_mlvj%s,model_VV_sb_lo_%s_mlvj%s,model_WW_EWK_sb_lo_%s_mlvj%s"%(self.channel,regionvbf,self.channel,regionvbf,self.channel,regionvbf,self.channel,regionvbf)), RooFit.Name("WW_EWK_line_invisible"), RooFit.LineColor(kBlack), RooFit.LineWidth(2), RooFit.VLines()) ;

        model_data.plotOn(mplot, RooFit.Components("model_TTbar_sb_lo_%s_mlvj%s,model_STop_sb_lo_%s_mlvj%s,model_VV_sb_lo_%s_mlvj%s"%(self.channel,regionvbf,self.channel,regionvbf,self.channel,regionvbf)),RooFit.Name("VV_line_invisible"), RooFit.LineColor(kBlack), RooFit.LineWidth(2), RooFit.VLines()) ;

        model_data.plotOn(mplot, RooFit.Components("model_TTbar_sb_lo_%s_mlvj%s,model_STop_sb_lo_%s_mlvj%s"%(self.channel,regionvbf,self.channel,regionvbf)),RooFit.Name("TTbar_line_invisible"), RooFit.LineColor(kBlack), RooFit.LineWidth(2), RooFit.VLines()) ;
         
        model_data.plotOn(mplot, RooFit.Components("model_STop_sb_lo_%s_mlvj%s"%(self.channel,regionvbf)), RooFit.Name("STop_line_invisible"), RooFit.LineColor(kBlack), RooFit.LineWidth(2), RooFit.VLines());


        rdataset_data_mlvj.plotOn(mplot,RooFit.Name("data"), RooFit.MarkerSize(1.5), RooFit.DataError(RooAbsData.SumW2), RooFit.XErrorSize(0) );

        ### draw the error band
        draw_error_band(rdataset_data_mlvj, model_data,self.workspace4fit_.var("rrv_number_data_sb_lo_%s_mlvj%s"%(self.channel,regionvbf)) ,rfresult,mplot,self.color_palet["Uncertainty"],"F");
        model_data.plotOn( mplot , RooFit.VLines(), RooFit.Invisible(), RooFit.LineColor(kBlack));
        model_data.plotOn( mplot , RooFit.Invisible(),RooFit.LineColor(kBlack));
        rdataset_data_mlvj.plotOn(mplot,RooFit.Name("data_invisible1"), RooFit.MarkerSize(1.5), RooFit.DataError(RooAbsData.SumW2), RooFit.XErrorSize(0) );

        mplot.GetYaxis().SetRangeUser(1e-2,mplot.GetMaximum()*1.2);

        ### Add the legend to the plot
        self.leg = self.legend4Plot(mplot,0,1,0., 0.06, 0.16, 0.);
        mplot.addObject(self.leg);

        ### get the pull plot and store the canvas
        mplot_pull = self.get_pull(rrv_mass_lvj,mplot);
        parameters_list = model_data.getParameters(rdataset_data_mlvj);

        ## CALCULATE CHI2
        datahist = rdataset_data_mlvj.binnedClone(rdataset_data_mlvj.GetName()+"_binnedClone",rdataset_data_mlvj.GetName()+"_binnedClone")
        Nbin = int(rrv_mass_lvj.getBins()); 
        rresult_param = rfresult.floatParsFinal();        
        nparameters =  rresult_param.getSize()                                         
        ChiSquare = model_data.createChi2(datahist,RooFit.Extended(kTRUE),RooFit.DataError(RooAbsData.Poisson));
        chi_over_ndf= ChiSquare.getVal()/(Nbin - nparameters);

        ## Add Chisquare to mplot_pull
        cs = TLatex(0.75,0.8,"#chi^{2}/ndf = %0.2f "%(float(chi_over_ndf)));
        cs.SetNDC();
        cs.SetTextSize(0.12);
        cs.AppendPad("same");
        mplot_pull.addObject(cs)

        self.file_out.write("\n fit_mlvj_in_Mj_sideband: nPar=%s, chiSquare=%s/%s"%(nparameters, ChiSquare.getVal(), Nbin - nparameters) );
        self.draw_canvas_with_pull( mplot, mplot_pull,parameters_list,"plots_%s_%s_%s_%s_g1/m_lvj_fitting%s/"%(options.additioninformation, self.channel,self.PS_model,self.wtagger_label,regionvbf), "m_lvj_sb_lo%s"%(label),"",1,1);

 
        #### Decorrelate the parameters in order to have a proper shape in the workspace
	wsfit_tmp = RooWorkspace("wsfit_tmp%s_sb_lo_from_fitting_mlvj%s"%(label,regionvbf));
        Deco      = PdfDiagonalizer("Deco%s_sb_lo_from_fitting_%s_%s_mlvj%s"%(label,self.channel,self.wtagger_label,regionvbf),wsfit_tmp,rfresult);
        print"#################### diagonalize data sideband fit "
	model_pdf_WJets_deco = Deco.diagonalize(model_pdf_WJets);
        print"#################### print parameters "
        model_pdf_WJets_deco.Print("v");
	model_pdf_WJets_deco.getParameters(rdataset_data_mlvj).Print("");
        getattr(self.workspace4fit_,"import")(model_pdf_WJets_deco);

        if not TString(label).Contains("_jes") and not TString(label).Contains("_jer") and not TString(label).Contains("WJets01") :

           mplot_sys = rrv_mass_lvj.frame( RooFit.Bins(int(rrv_mass_lvj.getBins()/self.narrow_factor)));           

           rdataset_data_mlvj.plotOn(mplot_sys, RooFit.Name("Data"), RooFit.MarkerSize(1.5), RooFit.DataError(RooAbsData.SumW2), RooFit.XErrorSize(0),RooFit.MarkerColor(0),RooFit.LineColor(0) );
           model_pdf_WJets_deco.plotOn(mplot_sys,RooFit.Name("Nominal"),RooFit.LineColor(kBlack));
           rrv_number_dataset = RooRealVar("rrv_number_dataset","rrv_number_dataset",rdataset_data_mlvj.sumEntries());
           rrv_number_dataset.setError(0.); ## only shape uncertainty
                            
           draw_error_band(rdataset_data_mlvj,model_pdf_WJets,rrv_number_dataset,rfresult,mplot,self.color_palet["Uncertainty"],"F");

           if self.workspace4fit_.pdf("model_pdf%smassvbf_jes_up_sb_lo_from_fitting_%s_mlvj%s_Deco%smassvbf_jes_up_sb_lo_from_fitting_%s_%s_mlvj%s"%(label,self.channel,regionvbf,label,self.channel,self.wtagger_label,regionvbf)) :
              self.workspace4fit_.pdf("model_pdf%smassvbf_jes_up_sb_lo_from_fitting_%s_mlvj%s_Deco%smassvbf_jes_up_sb_lo_from_fitting_%s_%s_mlvj%s"%(label,self.channel,regionvbf,label,self.channel,self.wtagger_label,regionvbf)).plotOn(mplot_sys,RooFit.Name("jes_up"), RooFit.LineColor(kBlue));

           if self.workspace4fit_.pdf("model_pdf%smassvbf_jes_dn_sb_lo_from_fitting_%s_mlvj%s_Deco%smassvbf_jes_dn_sb_lo_from_fitting_%s_%s_mlvj%s"%(label,self.channel,regionvbf,label,self.channel,self.wtagger_label,regionvbf)) :
              self.workspace4fit_.pdf("model_pdf%smassvbf_jes_dn_sb_lo_from_fitting_%s_mlvj%s_Deco%smassvbf_jes_dn_sb_lo_from_fitting_%s_%s_mlvj%s"%(label,self.channel,regionvbf,label,self.channel,self.wtagger_label,regionvbf)).plotOn(mplot_sys,RooFit.Name("jes_dn"), RooFit.LineColor(kRed));

           if self.workspace4fit_.pdf("model_pdf%smassvbf_jer_sb_lo_from_fitting_%s_mlvj%s_Deco%smassvbf_jer_sb_lo_from_fitting_%s_%s_mlvj%s"%(label,self.channel,regionvbf,label,self.channel,self.wtagger_label,regionvbf)) :
              self.workspace4fit_.pdf("model_pdf%smassvbf_jer_sb_lo_from_fitting_%s_mlvj%s_Deco%smassvbf_jer_sb_lo_from_fitting_%s_%s_mlvj%s"%(label,self.channel,regionvbf,label,self.channel,self.wtagger_label,regionvbf)).plotOn(mplot_sys,RooFit.Name("jer"), RooFit.LineColor(kAzure));

           if self.workspace4fit_.pdf("model_pdf%smassvbf_jer_up_sb_lo_from_fitting_%s_mlvj%s_Deco%smassvbf_jer_up_sb_lo_from_fitting_%s_%s_mlvj%s"%(label,self.channel,regionvbf,label,self.channel,self.wtagger_label,regionvbf)) :
              self.workspace4fit_.pdf("model_pdf%smassvbf_jer_up_sb_lo_from_fitting_%s_mlvj%s_Deco%smassvbf_jer_up_sb_lo_from_fitting_%s_%s_mlvj%s"%(label,self.channel,regionvbf,label,self.channel,self.wtagger_label,regionvbf)).plotOn(mplot_sys,RooFit.Name("jer_up"), RooFit.LineColor(kGreen+1));

           if self.workspace4fit_.pdf("model_pdf%smassvbf_jer_dn_sb_lo_from_fitting_%s_mlvj%s_Deco%smassvbf_jer_dn_sb_lo_from_fitting_%s_%s_mlvj%s"%(label,self.channel,regionvbf,label,self.channel,self.wtagger_label,regionvbf)) :
              self.workspace4fit_.pdf("model_pdf%smassvbf_jer_dn_sb_lo_from_fitting_%s_mlvj%s_Deco%smassvbf_jer_dn_sb_lo_from_fitting_%s_%s_mlvj%s"%(label,self.channel,regionvbf,label,self.channel,self.wtagger_label,regionvbf)).plotOn(mplot_sys,RooFit.Name("jer_dn"), RooFit.LineColor(6));

           if label == "_WJets0" and self.workspace4fit_.pdf("model_pdf_WJets01_sb_lo_from_fitting_%s_mlvj%s_Deco_WJets01_sb_lo_from_fitting_%s_%s_mlvj%s"%(self.channel,regionvbf,self.channel,self.wtagger_label,regionvbf)):
              self.workspace4fit_.pdf("model_pdf_WJets01_sb_lo_from_fitting_%s_mlvj%s_Deco_WJets01_sb_lo_from_fitting_%s_%s_mlvj%s"%(self.channel,regionvbf,self.channel,self.wtagger_label,regionvbf)).plotOn(mplot_sys,RooFit.Name("alt shape"), RooFit.LineColor(kOrange+1));

                        
           self.leg = self.legend4Plot(mplot_sys,0,1,0., 0.06, 0.16, 0.);
           mplot_sys.addObject(self.leg);
           mplot_sys.GetYaxis().SetRangeUser(1e-2,mplot_sys.GetMaximum()*1.2);

           self.draw_canvas_with_pull( mplot_sys, mplot_pull,parameters_list,"plots_%s_%s_%s_%s_g1/other/"%(options.additioninformation, self.channel,self.PS_model,self.wtagger_label), "m_lvj_sb_lo%s"%(label+regionvbf),"",1,1);


        #### Call the alpha evaluation in automatic
        self.get_WJets_mlvj_correction_sb_lo_to_signal_region(label,mlvj_model,"_mlvj"+regionvbf);

        ### Fix the pdf of signal, TTbar, STop and VV in the signal region         
        self.fix_Model("_%s"%(self.higgs_sample),"_signal_region","_mlvj");
        self.fix_Model("_%s"%(self.vbfhiggs_sample),"_signal_region","_mlvj");
        self.fix_Model("_TTbar","_signal_region","_mlvj",relaxed);
        self.fix_Model("_STop","_signal_region","_mlvj",relaxed);
        self.fix_Model("_VV","_signal_region","_mlvj",relaxed);
        self.fix_Model("_WW_EWK","_signal_region","_mlvj",relaxed);        

        ### Call the evaluation of the normalization in the signal region for signal, TTbar, VV, STop, and WJets after the extrapolation via alpha
        self.get_mlvj_normalization_insignalregion("_%s"%(self.higgs_sample));
        self.get_mlvj_normalization_insignalregion("_%s"%(self.vbfhiggs_sample));
        self.get_mlvj_normalization_insignalregion("_TTbar","",relaxed);
        self.get_mlvj_normalization_insignalregion("_STop","",relaxed);
        self.get_mlvj_normalization_insignalregion("_VV","",relaxed);
        self.get_mlvj_normalization_insignalregion("_WW_EWK","",relaxed);        
    
        self.get_mlvj_normalization_insignalregion(label,"model_pdf%s_signal_region_%s_after_correct_mlvj%s"%(label,self.channel,regionvbf));  

    ##### Function that calculate the normalization inside the mlvj signal region (mass window around the resonance in order to fill datacards)
    def get_mlvj_normalization_insignalregion(self, label, model_name="", relaxed = 0):

	print "############### get mlvj normalization inside SR ",label," ",model_name," ##################"

        if model_name == "" and relaxed == 0:
         model = self.workspace4fit_.pdf("model"+label+"_signal_region"+"_"+self.channel+"_mlvj");
        elif model_name == "" and relaxed == 1:
         model = self.workspace4fit_.pdf("model"+label+"_signal_region"+"_"+self.channel+"_mlvj_relaxed");            
	elif model_name != "" and relaxed == 0:
         model = self.workspace4fit_.pdf(model_name);
	elif model_name != "" and relaxed == 1:
         model = self.workspace4fit_.pdf(model_name+"_relaxed");

        rrv_mass_lvj = self.workspace4fit_.var("rrv_mass_lvj");

	fullInt   = model.createIntegral(RooArgSet(rrv_mass_lvj),RooArgSet(rrv_mass_lvj));
        signalInt = model.createIntegral(RooArgSet(rrv_mass_lvj),RooArgSet(rrv_mass_lvj),("signal_region"));

        fullInt_val = fullInt.getVal();
        signalInt_val = signalInt.getVal()/fullInt_val;

        ## integal in the signal region
        print "######### integral in SR: ",label+"signalInt=%s"%(signalInt_val);

        print "####### Events Number in MC Dataset:";
        self.workspace4fit_.var("rrv_number_dataset_signal_region"+label+"_"+self.channel+"_mlvj").Print();
        self.workspace4fit_.var("rrv_number_dataset_AllRange"+label+"_"+self.channel+"_mlvj").Print();

        print "########## Events Number get from fit:"
        if relaxed == 0:
         rrv_tmp = self.workspace4fit_.var("rrv_number"+label+"_signal_region"+"_"+self.channel+"_mlvj");
        else :
         rrv_tmp = self.workspace4fit_.var("rrv_number"+label+"_signal_region"+"_"+self.channel+"_mlvj_relaxed");
            
        print "Events Number in Signal Region from fitting: %s"%(rrv_tmp.getVal()*signalInt_val)

        #### store the info in the output file
        self.file_out.write( "\n%s++++++++++++++++++++++++++++++++++++"%(label) )
        self.file_out.write( "\nEvents Number in All Region from dataset : %s"%(self.workspace4fit_.var("rrv_number_dataset_AllRange"+label+"_"+self.channel+"_mlvj").getVal()) )
        self.file_out.write( "\nEvents Number in Signal Region from dataset: %s"%(self.workspace4fit_.var("rrv_number_dataset_signal_region"+label+"_"+self.channel+"_mlvj").getVal()) )
        self.file_out.write( "\nRatio signal_region/all_range from dataset :%s"%(self.workspace4fit_.var("rrv_number_dataset_signal_region"+label+"_"+self.channel+"_mlvj").getVal()/self.workspace4fit_.var("rrv_number_dataset_AllRange"+label+"_"+self.channel+"_mlvj").getVal() ) )
	self.file_out.write( "\nEvents Number in All Region from fitting : %s\n"%(rrv_tmp.getVal()) )
        self.file_out.write( "\nEvents Number in Signal Region from fitting: %s\n"%(rrv_tmp.getVal()*signalInt_val) )
        self.file_out.write( "\nRatio signal_region/all_range from fitting :%s"%(signalInt_val ) )

        if not self.workspace4fit_.var("rrv_number_fitting_signal_region"+label+"_"+self.channel+"_mlvj"):
         rrv_number_fitting_signal_region_mlvj = RooRealVar("rrv_number_fitting_signal_region"+label+"_"+self.channel+"_mlvj","rrv_number_fitting_signal_region"+label+"_"+self.channel+"_mlvj", rrv_tmp.getVal()*signalInt_val );
         getattr(self.workspace4fit_,"import")(rrv_number_fitting_signal_region_mlvj);
        else :
            self.workspace4fit_.var("rrv_number_fitting_signal_region"+label+"_"+self.channel+"_mlvj").setVal(rrv_tmp.getVal()*signalInt_val);

        self.workspace4fit_.var("rrv_number_fitting_signal_region"+label+"_"+self.channel+"_mlvj").Print();

    ### method to get the alpha function to extrapolate the wjets in the signal region
    def get_WJets_mlvj_correction_sb_lo_to_signal_region(self,label, mlvj_model, mass_spectrum="_mlvj"):

        print" ############# get the extrapolation function alpha from MC : ",label,"   ",mlvj_model,"   ",mass_spectrum," ###############";
        tmp_Style = self.tdrStyle.Clone("tmp_Style");
        tmp_Style.SetPadRightMargin(0.08);
        tmp_Style.SetPadTickY(0);
        tmp_Style.cd();

        ### take input var and datasets from 4fit collection --> mc not scaled to lumi --> just a shape here
        rrv_x = self.workspace4fit_.var("rrv_mass_lvj");
        rdataset_WJets_sb_lo_mlvj = self.workspace4fit_.data("rdataset4fit%s_sb_lo_%s"%(label,self.channel+mass_spectrum));
        rdataset_WJets_signal_region_mlvj = self.workspace4fit_.data("rdataset4fit%s_signal_region_%s"%(label,self.channel+mass_spectrum));

        ### create a frame for the next plots
        mplot = rrv_x.frame(RooFit.Title("correlation_pdf"), RooFit.Bins(int(rrv_x.getBins()/self.narrow_factor))) ;
        mplot.GetYaxis().SetTitle("arbitrary units");

        ### model used for Higgs analysis --> parameters in the SR has to be fitted, not yet done in order to take into account correlations between mj and mlvj
        
        if mlvj_model == "ErfExp_v1":

            rrv_c_sb       = self.workspace4fit_.var("rrv_c_ErfExp%s_sb_lo_%s"%(label,self.channel+mass_spectrum));
            rrv_offset_sb  = self.workspace4fit_.var("rrv_offset_ErfExp%s_sb_lo_%s"%(label,self.channel+mass_spectrum));            

            if mass_spectrum == "_mlvj_relaxed":
              rrv_width_sb   = self.workspace4fit_.var("rrv_width_ErfExp%s_sb_lo_%s"%(label,self.channel+mass_spectrum));
            else:
              rrv_width_sb   = self.workspace4fit_.var("rrv_width_ErfExp%s_signal_region_%s"%(label,self.channel+mass_spectrum));
              rrv_width_sb.setConstant(kTRUE);               

            rrv_delta_c = RooRealVar("rrv_delta_c_ErfExp%s_%s"%(label,self.channel+mass_spectrum),"rrv_delta_c_ErfExp%s_%s"%(label,self.channel+mass_spectrum),self.workspace4fit_.var("rrv_c_ErfExp%s_signal_region_%s"%(label,self.channel+mass_spectrum)).getVal()-rrv_c_sb.getVal(),self.workspace4fit_.var("rrv_c_ErfExp%s_signal_region_%s"%(label,self.channel+mass_spectrum)).getVal()-rrv_c_sb.getVal() -4*rrv_c_sb.getError(), self.workspace4fit_.var("rrv_c_ErfExp%s_signal_region_%s"%(label,self.channel+mass_spectrum)).getVal()-rrv_c_sb.getVal()+4*rrv_c_sb.getError());
            rrv_delta_offset = RooRealVar("rrv_delta_offset_ErfExp%s_%s"%(label,self.channel+mass_spectrum),"rrv_delta_offset_ErfExp%s_%s"%(label,self.channel+mass_spectrum),self.workspace4fit_.var("rrv_offset_ErfExp%s_signal_region_%s"%(label,self.channel+mass_spectrum)).getVal()-rrv_offset_sb.getVal(),self.workspace4fit_.var("rrv_offset_ErfExp%s_signal_region_%s"%(label,self.channel+mass_spectrum)).getVal()-rrv_offset_sb.getVal()-4*rrv_offset_sb.getError(), self.workspace4fit_.var("rrv_offset_ErfExp%s_signal_region_%s"%(label,self.channel+mass_spectrum)).getVal()-rrv_offset_sb.getVal()+rrv_offset_sb.getError());
            rrv_delta_width = RooRealVar("rrv_delta_width_ErfExp%s_%s"%(label,self.channel+mass_spectrum),"rrv_delta_width_ErfExp%s_%s"%(label,self.channel+mass_spectrum),self.workspace4fit_.var("rrv_width_ErfExp%s_signal_region_%s"%(label,self.channel+mass_spectrum)).getVal()-rrv_width_sb.getVal(),self.workspace4fit_.var("rrv_width_ErfExp%s_signal_region_%s"%(label,self.channel+mass_spectrum)).getVal()-rrv_width_sb.getVal() -4*rrv_width_sb.getError(),self.workspace4fit_.var("rrv_width_ErfExp%s_signal_region_%s"%(label,self.channel+mass_spectrum)).getVal()-rrv_width_sb.getVal()+4*rrv_width_sb.getError());

            rrv_c_sr      = RooFormulaVar("rrv_c_sr%s_%s"%(label,self.channel+mass_spectrum), "@0+@1",RooArgList(rrv_c_sb, rrv_delta_c ) );
            rrv_offset_sr = RooFormulaVar("rrv_offset_sr%s_%s"%(label,self.channel+mass_spectrum), "@0+@1",RooArgList(rrv_offset_sb, rrv_delta_offset ) );
            rrv_width_sr  = RooFormulaVar("rrv_width_sr%s_%s"%(label,self.channel+mass_spectrum), "@0+@1",RooArgList(rrv_width_sb, rrv_delta_width ) );

            correct_factor_pdf = RooAlpha("correct_factor_pdf","correct_factor_pdf", rrv_x, rrv_c_sr, rrv_offset_sr,rrv_width_sr, rrv_c_sb, rrv_offset_sb, rrv_width_sb, rrv_x.getMin(), rrv_x.getMax());

        if mlvj_model == "ErfPow_v1":

            rrv_c_sb      = self.workspace4fit_.var("rrv_c_ErfPow%s_sb_lo_%s"%(label,self.channel+mass_spectrum));
            rrv_offset_sb = self.workspace4fit_.var("rrv_offset_ErfPow%s_sb_lo_%s"%(label,self.channel+mass_spectrum));
            rrv_width_sb  = self.workspace4fit_.var("rrv_width_ErfPow%s_sb_lo_%s"%(label,self.channel+mass_spectrum));

            rrv_delta_c      = RooRealVar("rrv_delta_c_ErfPow%s_%s"%(label,self.channel+mass_spectrum),"rrv_delta_c_ErfPow%s_%s"%(label,self.channel+mass_spectrum),0.,-100*rrv_c_sb.getError(),100*rrv_c_sb.getError());
            rrv_delta_offset = RooRealVar("rrv_delta_offset_ErfPow%s_%s"%(label,self.channel+mass_spectrum),"rrv_delta_offset_ErfPow%s_%s"%(label,self.channel+mass_spectrum),0.,-100*rrv_offset_sb.getError(),100*rrv_offset_sb.getError());
 
            rrv_delta_width  = RooRealVar("rrv_delta_width_ErfPow%s_%s"%(label,self.channel+mass_spectrum),"rrv_delta_width_ErfPow%s_%s"%(label,self.channel+mass_spectrum),0.,-100*rrv_width_sb.getError(),100*rrv_width_sb.getError());

            rrv_c_sr      = RooFormulaVar("rrv_c_sr%s_%s"%(label,self.channel+mass_spectrum), "@0+@1",RooArgList(rrv_c_sb, rrv_delta_c ) );
            rrv_offset_sr = RooFormulaVar("rrv_offset_sr%s_%s"%(label,self.channel+mass_spectrum), "@0+@1",RooArgList(rrv_offset_sb, rrv_delta_offset ) );
            rrv_width_sr  = RooFormulaVar("rrv_width_sr%s_%s"%(label,self.channel+mass_spectrum), "@0+@1",RooArgList(rrv_width_sb, rrv_delta_width ) );

            correct_factor_pdf = RooAlpha4ErfPowPdf("correct_factor_pdf","correct_factor_pdf", rrv_x, rrv_c_sr, rrv_offset_sr,rrv_width_sr, rrv_c_sb, rrv_offset_sb, rrv_width_sb);

        if mlvj_model == "ErfPow2_v1":

            rrv_c0_sb     = self.workspace4fit_.var("rrv_c0_ErfPow2%s_sb_lo_%s"%(label,self.channel+mass_spectrum));
            rrv_c1_sb     = self.workspace4fit_.var("rrv_c1_ErfPow2%s_sb_lo_%s"%(label,self.channel+mass_spectrum));
            rrv_offset_sb = self.workspace4fit_.var("rrv_offset_ErfPow2%s_sb_lo_%s"%(label,self.channel+mass_spectrum));

            if mass_spectrum == "_mlvj_relaxed":
                rrv_width_sb   = self.workspace4fit_.var("rrv_width_ErfPow2%s_sb_lo_%s"%(label,self.channel+mass_spectrum));
            else:
                rrv_width_sb   = self.workspace4fit_.var("rrv_width_ErfPow2%s_signal_region_%s"%(label,self.channel+mass_spectrum));
                rrv_width_sb.setConstant(kTRUE);

            rrv_delta_c0      = RooRealVar("rrv_delta_c0_ErfPow2%s_%s"%(label,self.channel+mass_spectrum),"rrv_delta_c0_ErfPow2%s_%s"%(label,self.channel+mass_spectrum),self.workspace4fit_.var("rrv_c0_ErfPow2%s_signal_region_%s"%(label,self.channel+mass_spectrum)).getVal()-rrv_c0_sb.getVal(),self.workspace4fit_.var("rrv_c0_ErfPow2%s_signal_region_%s"%(label,self.channel+mass_spectrum)).getVal()-rrv_c0_sb.getVal() -4*rrv_c0_sb.getError(), self.workspace4fit_.var("rrv_c0_ErfPow2%s_signal_region_%s"%(label,self.channel+mass_spectrum)).getVal()-rrv_c0_sb.getVal()+4*rrv_c0_sb.getError());

            rrv_delta_c1      = RooRealVar("rrv_delta_c1_ErfPow2%s_%s"%(label,self.channel+mass_spectrum),"rrv_delta_c1_ErfPow2%s_%s"%(label,self.channel+mass_spectrum),self.workspace4fit_.var("rrv_c1_ErfPow2%s_signal_region_%s"%(label,self.channel+mass_spectrum)).getVal()-rrv_c1_sb.getVal(),self.workspace4fit_.var("rrv_c1_ErfPow2%s_signal_region_%s"%(label,self.channel+mass_spectrum)).getVal()-rrv_c1_sb.getVal() -4*rrv_c1_sb.getError(), self.workspace4fit_.var("rrv_c1_ErfPow2%s_signal_region_%s"%(label,self.channel+mass_spectrum)).getVal()-rrv_c1_sb.getVal()+4*rrv_c1_sb.getError());

            rrv_delta_offset      = RooRealVar("rrv_delta_offset_ErfPow2%s_%s"%(label,self.channel+mass_spectrum),"rrv_delta_offset_ErfPow2%s_%s"%(label,self.channel+mass_spectrum),self.workspace4fit_.var("rrv_offset_ErfPow2%s_signal_region_%s"%(label,self.channel+mass_spectrum)).getVal()-rrv_offset_sb.getVal(),self.workspace4fit_.var("rrv_offset_ErfPow2%s_signal_region_%s"%(label,self.channel+mass_spectrum)).getVal()-rrv_offset_sb.getVal() -4*rrv_offset_sb.getError(), self.workspace4fit_.var("rrv_offset_ErfPow2%s_signal_region_%s"%(label,self.channel+mass_spectrum)).getVal()-rrv_offset_sb.getVal()+4*rrv_offset_sb.getError());            

            rrv_delta_width      = RooRealVar("rrv_delta_width_ErfPow2%s_%s"%(label,self.channel+mass_spectrum),"rrv_delta_width_ErfPow2%s_%s"%(label,self.channel+mass_spectrum),self.workspace4fit_.var("rrv_width_ErfPow2%s_signal_region_%s"%(label,self.channel+mass_spectrum)).getVal()-rrv_width_sb.getVal(),self.workspace4fit_.var("rrv_width_ErfPow2%s_signal_region_%s"%(label,self.channel+mass_spectrum)).getVal()-rrv_width_sb.getVal() -4*rrv_width_sb.getError(), self.workspace4fit_.var("rrv_width_ErfPow2%s_signal_region_%s"%(label,self.channel+mass_spectrum)).getVal()-rrv_width_sb.getVal()+4*rrv_width_sb.getError());
                
            rrv_c0_sr     = RooFormulaVar("rrv_c0_sr%s_%s"%(label,self.channel+mass_spectrum), "@0+@1",RooArgList(rrv_c0_sb, rrv_delta_c0 ) );
            rrv_c1_sr     = RooFormulaVar("rrv_c1_sr%s_%s"%(label,self.channel+mass_spectrum), "@0+@1",RooArgList(rrv_c1_sb, rrv_delta_c1 ) );
            rrv_offset_sr = RooFormulaVar("rrv_offset_sr%s_%s"%(label,self.channel+mass_spectrum), "@0+@1",RooArgList(rrv_offset_sb, rrv_delta_offset ) );
            rrv_width_sr  = RooFormulaVar("rrv_width_sr%s_%s"%(label,self.channel+mass_spectrum), "@0+@1",RooArgList(rrv_width_sb, rrv_delta_width ) );

            correct_factor_pdf = RooAlpha4ErfPow2Pdf("correct_factor_pdf","correct_factor_pdf", rrv_x, rrv_c0_sr, rrv_c1_sr, rrv_offset_sr,rrv_width_sr, rrv_c0_sb, rrv_c1_sb, rrv_offset_sb, rrv_width_sb);

        if mlvj_model == "ErfPowExp_v1": ## take initial value from what was already fitted in the SR

            rrv_c0_sb     = self.workspace4fit_.var("rrv_c0_ErfPowExp%s_sb_lo_%s"%(label,self.channel+mass_spectrum));
            rrv_c1_sb     = self.workspace4fit_.var("rrv_c1_ErfPowExp%s_sb_lo_%s"%(label,self.channel+mass_spectrum));
            rrv_offset_sb = self.workspace4fit_.var("rrv_offset_ErfPowExp%s_sb_lo_%s"%(label,self.channel+mass_spectrum));

            if mass_spectrum == "_mlvj_relaxed":
                rrv_width_sb   = self.workspace4fit_.var("rrv_width_ErfPowExp%s_sb_lo_%s"%(label,self.channel+mass_spectrum));

            else:
                rrv_width_sb   = self.workspace4fit_.var("rrv_width_ErfPowExp%s_signal_region_%s"%(label,self.channel+mass_spectrum));
                rrv_width_sb.setConstant(kTRUE);               

            rrv_delta_c0  = RooRealVar("rrv_delta_c0_ErfPowExp%s_%s"%(label,self.channel+mass_spectrum),"rrv_delta_c0_ErfPowExp%s_%s"%(label,self.channel+mass_spectrum),
                                        self.workspace4fit_.var("rrv_c0_ErfPowExp%s_signal_region_%s"%(label,self.channel+mass_spectrum)).getVal()-rrv_c0_sb.getVal(),
                                        self.workspace4fit_.var("rrv_c0_ErfPowExp%s_signal_region_%s"%(label,self.channel+mass_spectrum)).getVal()-rrv_c0_sb.getVal()-4*rrv_c0_sb.getError(),self.workspace4fit_.var("rrv_c0_ErfPowExp%s_signal_region_%s"%(label,self.channel+mass_spectrum)).getVal()-rrv_c0_sb.getVal()+4*rrv_c0_sb.getError() )

            rrv_delta_c1 = RooRealVar("rrv_delta_c1_ErfPowExp%s_%s"%(label,self.channel),"rrv_delta_c1_ErfPowExp%s_%s"%(label,self.channel+mass_spectrum),
                                       self.workspace4fit_.var("rrv_c1_ErfPowExp%s_signal_region_%s"%(label,self.channel+mass_spectrum)).getVal()-rrv_c1_sb.getVal(),
                                       self.workspace4fit_.var("rrv_c1_ErfPowExp%s_signal_region_%s"%(label,self.channel+mass_spectrum)).getVal()-rrv_c1_sb.getVal()-4*rrv_c1_sb.getError(),self.workspace4fit_.var("rrv_c1_ErfPowExp%s_signal_region_%s"%(label,self.channel+mass_spectrum)).getVal()-rrv_c1_sb.getVal()+4*rrv_c1_sb.getError() )

            rrv_delta_offset = RooRealVar("rrv_delta_offset_ErfPowExp%s_%s"%(label,self.channel+mass_spectrum),"rrv_delta_offset_ErfPowExp%s_%s"%(label,self.channel+mass_spectrum),
                                       self.workspace4fit_.var("rrv_offset_ErfPowExp%s_signal_region_%s"%(label,self.channel+mass_spectrum)).getVal()-rrv_offset_sb.getVal(),
                                       self.workspace4fit_.var("rrv_offset_ErfPowExp%s_signal_region_%s"%(label,self.channel+mass_spectrum)).getVal()-rrv_offset_sb.getVal()-4*rrv_offset_sb.getError(),self.workspace4fit_.var("rrv_offset_ErfPowExp%s_signal_region_%s"%(label,self.channel+mass_spectrum)).getVal()-rrv_offset_sb.getVal()+4*rrv_offset_sb.getError())

            rrv_delta_width = RooRealVar("rrv_delta_width_ErfPowExp%s_%s"%(label,self.channel+mass_spectrum),"rrv_delta_width_ErfPowExp%s_%s"%(label,self.channel+mass_spectrum),
                                         self.workspace4fit_.var("rrv_width_ErfPowExp%s_signal_region_%s"%(label,self.channel+mass_spectrum)).getVal()-rrv_width_sb.getVal(),
                                         self.workspace4fit_.var("rrv_width_ErfPowExp%s_signal_region_%s"%(label,self.channel+mass_spectrum)).getVal()-rrv_width_sb.getVal()-4*rrv_width_sb.getError(),self.workspace4fit_.var("rrv_width_ErfPowExp%s_signal_region_%s"%(label,self.channel+mass_spectrum)).getVal()-rrv_width_sb.getVal()+4*rrv_width_sb.getError() );

            rrv_c0_sr     = RooFormulaVar("rrv_c0_sr%s_%s"%(label,self.channel+mass_spectrum), "@0+@1",RooArgList(rrv_c0_sb, rrv_delta_c0 ) );
            rrv_c1_sr     = RooFormulaVar("rrv_c1_sr%s_%s"%(label,self.channel+mass_spectrum), "@0+@1",RooArgList(rrv_c1_sb, rrv_delta_c1 ) );
            rrv_offset_sr = RooFormulaVar("rrv_offset_sr%s_%s"%(label,self.channel+mass_spectrum), "@0+@1",RooArgList(rrv_offset_sb, rrv_delta_offset ) );
            rrv_width_sr  = RooFormulaVar("rrv_width_sr%s_%s"%(label,self.channel+mass_spectrum), "@0+@1",RooArgList(rrv_width_sb, rrv_delta_width ) );

            correct_factor_pdf = RooAlpha4ErfPowExpPdf("correct_factor_pdf","correct_factor_pdf", rrv_x, rrv_c0_sr, rrv_c1_sr, rrv_offset_sr,rrv_width_sr, rrv_c0_sb, rrv_c1_sb, rrv_offset_sb, rrv_width_sb);

        if mlvj_model == "Exp":
            rrv_c_sb    = self.workspace4fit_.var("rrv_c_Exp%s_sb_lo_%s"%(label,self.channel+mass_spectrum));
            rrv_delta_c = RooRealVar("rrv_delta_c_Exp%s_%s"%(label,self.channel+mass_spectrum),"rrv_delta_c_Exp%s_%s"%(label,self.channel+mass_spectrum),
                                      self.workspace4fit_.var("rrv_c_Exp%s_signal_region_%s"%(label,self.channel+mass_spectrum)).getVal()-rrv_c_sb.getVal(),
                                      self.workspace4fit_.var("rrv_c_Exp%s_signal_region_%s"%(label,self.channel+mass_spectrum)).getVal()-rrv_c_sb.getVal()-4*rrv_c_sb.getError(),
                                      self.workspace4fit_.var("rrv_c_Exp%s_signal_region_%s"%(label,self.channel+mass_spectrum)).getVal()-rrv_c_sb.getVal()+4*rrv_c_sb.getError() )

            correct_factor_pdf = RooExponential("correct_factor_pdf","correct_factor_pdf",rrv_x,rrv_delta_c);

        if mlvj_model == "2Exp":
            rrv_c0_sb    = self.workspace4fit_.var("rrv_c0_2Exp%s_sb_lo_%s"%(label,self.channel+mass_spectrum));
            rrv_delta_c0 = RooRealVar("rrv_delta_c0_2Exp%s_%s"%(label,self.channel+mass_spectrum),"rrv_delta_c0_2Exp%s_%s"%(label,self.channel+mass_spectrum),
                                       self.workspace4fit_.var("rrv_c0_2Exp%s_signal_region_%s"%(label,self.channel+mass_spectrum)).getVal()-rrv_c0_sb.getVal(),
                                       self.workspace4fit_.var("rrv_c0_2Exp%s_signal_region_%s"%(label,self.channel+mass_spectrum)).getVal()-rrv_c0_sb.getVal()-4*rrv_c0_sb.getError(),
                                       self.workspace4fit_.var("rrv_c0_2Exp%s_signal_region_%s"%(label,self.channel+mass_spectrum)).getVal()-rrv_c0_sb.getVal()+4*rrv_c0_sb.getError() )

            rrv_c1_sb = self.workspace4fit_.var("rrv_c1_2Exp%s_sb_lo_%s"%(label,self.channel+mass_spectrum));
            rrv_delta_c1 = RooRealVar("rrv_delta_c1_2Exp%s_%s"%(label,self.channel+mass_spectrum),"rrv_delta_c1_2Exp%s_%s"%(label,self.channel+mass_spectrum),
                                       self.workspace4fit_.var("rrv_c1_2Exp%s_signal_region_%s"%(label,self.channel+mass_spectrum)).getVal()-rrv_c1_sb.getVal(),
                                       self.workspace4fit_.var("rrv_c1_2Exp%s_signal_region_%s"%(label,self.channel+mass_spectrum)).getVal()-rrv_c1_sb.getVal()-4*rrv_c1_sb.getError(),
                                       self.workspace4fit_.var("rrv_c1_2Exp%s_signal_region_%s"%(label,self.channel+mass_spectrum)).getVal()-rrv_c1_sb.getVal()+4*rrv_c1_sb.getError() )

            rrv_frac_sb    = self.workspace4fit_.var("rrv_frac_2Exp%s_sb_lo_%s"%(label,self.channel+mass_spectrum));
            rrv_delta_frac = RooRealVar("rrv_delta_frac_2Exp%s_%s"%(label,self.channel+mass_spectrum),"rrv_delta_frac_2Exp%s_%s"%(label,self.channel+mass_spectrum),
                                         self.workspace4fit_.var("rrv_frac_2Exp%s_signal_region_%s"%(label,self.channel+mass_spectrum)).getVal()-rrv_frac_sb.getVal(),
                                         self.workspace4fit_.var("rrv_frac_2Exp%s_signal_region_%s"%(label,self.channel+mass_spectrum)).getVal()-rrv_frac_sb.getVal()-4*rrv_frac_sb.getError(),
                                         self.workspace4fit_.var("rrv_frac_2Exp%s_signal_region_%s"%(label,self.channel+mass_spectrum)).getVal()-rrv_frac_sb.getVal()+4*rrv_frac_sb.getError() )

            rrv_c0_sr = RooFormulaVar("rrv_c0_2Exp_sr%s_%s"%(label,self.channel+mass_spectrum), "@0+@1",RooArgList(rrv_c0_sb, rrv_delta_c0 ) );
            rrv_c1_sr = RooFormulaVar("rrv_c1_2Exp_sr%s_%s"%(label,self.channel+mass_spectrum), "@0+@1",RooArgList(rrv_c1_sb, rrv_delta_c1 ) );
            rrv_frac_sr = RooFormulaVar("rrv_frac_2Exp_sr%s_%s"%(label,self.channel+mass_spectrum), "@0+@1",RooArgList(rrv_frac_sb, rrv_delta_frac ) );

            correct_factor_pdf = RooAlpha42ExpPdf("correct_factor_pdf","correct_factor_pdf",rrv_x,rrv_c0_sr,rrv_c1_sr,rrv_frac_sr, rrv_c0_sb,rrv_c1_sb,rrv_frac_sb );

        if mlvj_model=="Pow":

            rrv_c_sb    = self.workspace4fit_.var("rrv_c_Pow%s_sb_lo_%s"%(label,self.channel+mass_spectrum));
            rrv_delta_c = RooRealVar("rrv_delta_c_Pow%s_%s"%(label,self.channel+mass_spectrum),"rrv_delta_c_Pow%s_%s"%(label,self.channel+mass_spectrum),0., -100*rrv_c_sb.getError(),100*rrv_c_sb.getError());
            correct_factor_pdf = RooPowPdf("correct_factor_pdf","correct_factor_pdf",rrv_x,rrv_delta_c);

        if mlvj_model=="ExpN":
            rrv_c_sb  = self.workspace4fit_.var("rrv_c_ExpN%s_sb_lo_%s"%(label,self.channel+mass_spectrum));
            rrv_n_sb  = self.workspace4fit_.var("rrv_n_ExpN%s_sb_lo_%s"%(label,self.channel+mass_spectrum));
            rrv_delta_c = RooRealVar("rrv_delta_c_ExpN%s_%s"%(label,self.channel+mass_spectrum),"rrv_delta_c_ExpN%s_%s"%(label,self.channel+mass_spectrum),
                                      self.workspace4fit_.var("rrv_c_ExpN%s_signal_region_%s"%(label,self.channel+mass_spectrum)).getVal()-rrv_c_sb.getVal(),
                                      self.workspace4fit_.var("rrv_c_ExpN%s_signal_region_%s"%(label,self.channel+mass_spectrum)).getVal()-rrv_c_sb.getVal()-4*rrv_c_sb.getError(),
                                      self.workspace4fit_.var("rrv_c_ExpN%s_signal_region_%s"%(label,self.channel+mass_spectrum)).getVal()-rrv_c_sb.getVal()+4*rrv_c_sb.getError() )
            rrv_delta_n = RooRealVar("rrv_delta_n_ExpN%s_%s"%(label,self.channel+mass_spectrum),"rrv_delta_n_ExpN%s_%s"%(label,self.channel+mass_spectrum),
                                      self.workspace4fit_.var("rrv_n_ExpN%s_signal_region_%s"%(label,self.channel+mass_spectrum)).getVal()-rrv_n_sb.getVal(),
                                      self.workspace4fit_.var("rrv_n_ExpN%s_signal_region_%s"%(label,self.channel+mass_spectrum)).getVal()-rrv_n_sb.getVal()-4*rrv_n_sb.getError(),
                                      self.workspace4fit_.var("rrv_n_ExpN%s_signal_region_%s"%(label,self.channel+mass_spectrum)).getVal()-rrv_n_sb.getVal()+4*rrv_n_sb.getError() )

            correct_factor_pdf = RooExpNPdf("correct_factor_pdf","correct_factor_pdf",rrv_x,rrv_delta_c, rrv_delta_n);

        if mlvj_model=="ExpTail":
            rrv_s_sb =self.workspace4fit_.var("rrv_s_ExpTail%s_sb_lo_%s"%(label,self.channel+mass_spectrum));
            rrv_a_sb =self.workspace4fit_.var("rrv_a_ExpTail%s_sb_lo_%s"%(label,self.channel+mass_spectrum));

            rrv_delta_s = RooRealVar("rrv_delta_s_ExpTail%s_%s"%(label,self.channel+mass_spectrum),"rrv_delta_s_ExpTail%s_%s"%(label,self.channel+mass_spectrum),
                                      self.workspace4fit_.var("rrv_s_ExpTail%s_signal_region_%s"%(label,self.channel+mass_spectrum)).getVal()-rrv_s_sb.getVal(),
                                      self.workspace4fit_.var("rrv_s_ExpTail%s_signal_region_%s"%(label,self.channel+mass_spectrum)).getVal()-rrv_s_sb.getVal()-4*rrv_s_sb.getError(),
                                      self.workspace4fit_.var("rrv_s_ExpTail%s_signal_region_%s"%(label,self.channel+mass_spectrum)).getVal()-rrv_s_sb.getVal()+4*rrv_s_sb.getError() )
            rrv_delta_a = RooRealVar("rrv_delta_a_ExpTail%s_%s"%(label,self.channel+mass_spectrum),"rrv_delta_a_ExpTail%s_%s"%(label,self.channel+mass_spectrum),
                                      self.workspace4fit_.var("rrv_a_ExpTail%s_signal_region_%s"%(label,self.channel+mass_spectrum)).getVal()-rrv_a_sb.getVal(),
                                      self.workspace4fit_.var("rrv_a_ExpTail%s_signal_region_%s"%(label,self.channel+mass_spectrum)).getVal()-rrv_a_sb.getVal()-4*rrv_a_sb.getError(),
                                      self.workspace4fit_.var("rrv_a_ExpTail%s_signal_region_%s"%(label,self.channel+mass_spectrum)).getVal()-rrv_a_sb.getVal()+4*rrv_a_sb.getError() )

            rrv_a_sr = RooFormulaVar("rrv_a_ExpTail_sr%s_%s"%(label,self.channel+mass_spectrum), "@0+@1",RooArgList(rrv_a_sb, rrv_delta_a ) );
            rrv_s_sr = RooFormulaVar("rrv_s_ExpTail_sr%s_%s"%(label,self.channel+mass_spectrum), "@0+@1",RooArgList(rrv_s_sb, rrv_delta_s ) );

            correct_factor_pdf = RooAlpha4ExpTailPdf("correct_factor_pdf","correct_factor_pdf",rrv_x,rrv_s_sr, rrv_a_sr, rrv_s_sb, rrv_a_sb);

        if mlvj_model=="Pow2":

            rrv_c0_sb    = self.workspace4fit_.var("rrv_c0_Pow2%s_sb_lo_%s"%(label,self.channel+mass_spectrum));
            rrv_c1_sb    = self.workspace4fit_.var("rrv_c1_Pow2%s_sb_lo_%s"%(label,self.channel+mass_spectrum));
            rrv_delta_c0 = RooRealVar("rrv_delta_c0_Pow2%s_%s"%(label,self.channel+mass_spectrum),"rrv_delta_c0_Pow2%s_%s"%(label,self.channel+mass_spectrum),0., -100*rrv_c0_sb.getError(),100*rrv_c0_sb.getError());
            rrv_delta_c1 = RooRealVar("rrv_delta_c1_Pow2%s_%s"%(label,self.channel+mass_spectrum),"rrv_delta_c1_Pow2%s_%s"%(label,self.channel+mass_spectrum),0., -100*rrv_c1_sb.getError(),100*rrv_c1_sb.getError());
            correct_factor_pdf = RooPow2Pdf("correct_factor_pdf","correct_factor_pdf",rrv_x,rrv_delta_c0,rrv_delta_c1);


        ### define the category and do the simultaneous fit taking the combined dataset of events in mlvj sb and sr

        data_category = RooCategory("data_category","data_category");
        data_category.defineType("sideband");
        data_category.defineType("signal_region");

        if mass_spectrum == "_mlvj_relaxed":
           combData4fit = self.workspace4fit_.data("combData4fit%s_%s"%(label,self.channel+"_relaxed"));
        else:
           combData4fit = self.workspace4fit_.data("combData4fit%s_%s"%(label,self.channel));           

        model_pdf_sb_lo_WJets         = self.workspace4fit_.pdf("model_pdf%s_sb_lo_%s"%(label,self.channel+mass_spectrum));
        model_pdf_signal_region_WJets = RooProdPdf("model_pdf%s_signal_region_%s"%(label,self.channel+mass_spectrum),"model_pdf%s_signal_region_%s"%(label,self.channel+mass_spectrum) ,model_pdf_sb_lo_WJets,correct_factor_pdf);

        simPdf = RooSimultaneous("simPdf","simPdf",data_category);
        simPdf.addPdf(model_pdf_sb_lo_WJets,"sideband");
        simPdf.addPdf(model_pdf_signal_region_WJets,"signal_region");
        rfresult = simPdf.fitTo(combData4fit,RooFit.Save(kTRUE), RooFit.SumW2Error(kTRUE));
        rfresult = simPdf.fitTo(combData4fit,RooFit.Save(kTRUE), RooFit.SumW2Error(kTRUE), RooFit.Minimizer("Minuit2"));
        rfresult.Print();
        rfresult.covarianceMatrix().Print();

        ### Decorrelate the parameters in the alpha shape
        wsfit_tmp = RooWorkspace("wsfit_tmp%s_sim%s"%(label,mass_spectrum));
        print "############### diagonalizer alpha ";
        Deco      = PdfDiagonalizer("Deco%s_sim_%s_%s"%(label,self.channel,self.wtagger_label+mass_spectrum),wsfit_tmp,rfresult);
        correct_factor_pdf_deco = Deco.diagonalize(correct_factor_pdf);
        correct_factor_pdf_deco.Print();
       
        correct_factor_pdf_deco.getParameters(rdataset_WJets_signal_region_mlvj).Print("v");
        getattr(self.workspace4fit_,"import")(correct_factor_pdf_deco);

        ## in case of default Wjets with default shape
        if label == "_WJets0":

            ### only mc plots in the SB region
            mplot_sb_lo = rrv_x.frame(RooFit.Title("WJets sb low"), RooFit.Bins(int(rrv_x.getBins()/self.narrow_factor)));

            ## plot just W+Jets sb distribution
            rdataset_WJets_sb_lo_mlvj.plotOn(mplot_sb_lo, RooFit.MarkerSize(1.5), RooFit.DataError(RooAbsData.SumW2), RooFit.XErrorSize(0) );
            model_pdf_sb_lo_WJets.plotOn(mplot_sb_lo);
            mplot_pull_sideband = self.get_pull(rrv_x,mplot_sb_lo);

            parameters_list     = model_pdf_sb_lo_WJets.getParameters(rdataset_WJets_sb_lo_mlvj);
            mplot_sb_lo.GetYaxis().SetRangeUser(1e-2,mplot_sb_lo.GetMaximum()*1.2);

            if mass_spectrum == "_mlvj_relaxed":
                self.draw_canvas_with_pull( mplot_sb_lo, mplot_pull_sideband,parameters_list,"plots_%s_%s_%s_%s_g1/other_relaxed/"%(options.additioninformation, self.channel,self.PS_model,self.wtagger_label), "m_lvj%s_sb_lo_sim"%(label),"",1,1)
            else:
                self.draw_canvas_with_pull( mplot_sb_lo, mplot_pull_sideband,parameters_list,"plots_%s_%s_%s_%s_g1/other/"%(options.additioninformation, self.channel,self.PS_model,self.wtagger_label), "m_lvj%s_sb_lo_sim"%(label),"",1,1)                

            ### only W+jets mc plots in the SR region
            mplot_signal_region = rrv_x.frame(RooFit.Title("WJets sr"), RooFit.Bins(int(rrv_x.getBins()/self.narrow_factor)));

            rdataset_WJets_signal_region_mlvj.plotOn(mplot_signal_region, RooFit.MarkerSize(1.5), RooFit.DataError(RooAbsData.SumW2), RooFit.XErrorSize(0) );
            model_pdf_signal_region_WJets.plotOn(mplot_signal_region);
            mplot_pull_signal_region = self.get_pull(rrv_x, mplot_signal_region);

            parameters_list = model_pdf_signal_region_WJets.getParameters(rdataset_WJets_signal_region_mlvj);
            mplot_signal_region.GetYaxis().SetRangeUser(1e-2,mplot_signal_region.GetMaximum()*1.2);

            if mass_spectrum == "_mlvj_relaxed":
                self.draw_canvas_with_pull( mplot_signal_region, mplot_pull_signal_region,parameters_list,"plots_%s_%s_%s_%s_g1/other_relaxed/"%(options.additioninformation, self.channel,self.PS_model,self.wtagger_label), "m_lvj%s_signal_region_sim"%(label),"",1,1);
            else:
                self.draw_canvas_with_pull( mplot_signal_region, mplot_pull_signal_region,parameters_list,"plots_%s_%s_%s_%s_g1/other/"%(options.additioninformation, self.channel,self.PS_model,self.wtagger_label), "m_lvj%s_signal_region_sim"%(label),"",1,1);
                


        ### plot also what is get from other source if available : alternate PS and shape: 1 PS and 01 is shape or fitting function
        if label == "_WJets0":
            ### Total plot shape in sb_lo, sr and alpha
            model_pdf_sb_lo_WJets.plotOn(mplot,RooFit.Name("Sideband"),RooFit.LineStyle(10));
            model_pdf_signal_region_WJets.plotOn(mplot, RooFit.LineColor(kRed) ,RooFit.LineStyle(8), RooFit.Name("Signal Region"));
            correct_factor_pdf_deco.plotOn(mplot, RooFit.LineColor(kBlack),RooFit.Name("#alpha") );

            if self.workspace4fit_.pdf("correct_factor_pdf_Deco_WJets1_sim_%s_%s"%(self.channel,self.wtagger_label+mass_spectrum)):
                self.workspace4fit_.pdf("correct_factor_pdf_Deco_WJets1_sim_%s_%s"%(self.channel,self.wtagger_label+mass_spectrum)).plotOn(mplot, RooFit.LineColor(kOrange), RooFit.LineStyle(3),RooFit.Name("#alpha: Alternate PS") );

            if self.workspace4fit_.pdf("correct_factor_pdf_Deco_WJets01_sim_%s_%s"%(self.channel, self.wtagger_label+mass_spectrum)):
                self.workspace4fit_.pdf("correct_factor_pdf_Deco_WJets01_sim_%s_%s"%(self.channel, self.wtagger_label+mass_spectrum)).plotOn(mplot, RooFit.LineColor(kMagenta), RooFit.LineStyle(7),RooFit.Name("#alpha: Alternate Function") );

            if self.workspace4fit_.pdf("correct_factor_pdf_Deco_WJets0massvbf_jes_up_sim_%s_%s"%(self.channel, self.wtagger_label+mass_spectrum)):
                self.workspace4fit_.pdf("correct_factor_pdf_Deco_WJets0massvbf_jes_up_sim_%s_%s"%(self.channel, self.wtagger_label+mass_spectrum)).plotOn(mplot, RooFit.LineColor(kRed), RooFit.LineStyle(3),RooFit.Name("#alpha: jes up") );

            if self.workspace4fit_.pdf("correct_factor_pdf_Deco_WJets0massvbf_jes_dn_sim_%s_%s"%(self.channel, self.wtagger_label+mass_spectrum)):
                self.workspace4fit_.pdf("correct_factor_pdf_Deco_WJets0massvbf_jes_dn_sim_%s_%s"%(self.channel, self.wtagger_label+mass_spectrum)).plotOn(mplot, RooFit.LineColor(kOrange+1), RooFit.LineStyle(7),RooFit.Name("#alpha: jes dn") );

            if self.workspace4fit_.pdf("correct_factor_pdf_Deco_WJets0massvbf_jer_sim_%s_%s"%(self.channel, self.wtagger_label+mass_spectrum)):
                self.workspace4fit_.pdf("correct_factor_pdf_Deco_WJets0massvbf_jer_sim_%s_%s"%(self.channel, self.wtagger_label+mass_spectrum)).plotOn(mplot, RooFit.LineColor(kAzure), RooFit.LineStyle(3),RooFit.Name("#alpha: jer") );

            if self.workspace4fit_.pdf("correct_factor_pdf_Deco_WJets0massvbf_jer_up_sim_%s_%s"%(self.channel, self.wtagger_label+mass_spectrum)):
                self.workspace4fit_.pdf("correct_factor_pdf_Deco_WJets0massvbf_jes_up_sim_%s_%s"%(self.channel, self.wtagger_label+mass_spectrum)).plotOn(mplot, RooFit.LineColor(kYellow+1), RooFit.LineStyle(7),RooFit.Name("#alpha: jer up") );

            if self.workspace4fit_.pdf("correct_factor_pdf_Deco_WJets0massvbf_jer_dn_sim_%s_%s"%(self.channel, self.wtagger_label+mass_spectrum)):
                self.workspace4fit_.pdf("correct_factor_pdf_Deco_WJets0massvbf_jes_dn_sim_%s_%s"%(self.channel, self.wtagger_label+mass_spectrum)).plotOn(mplot, RooFit.LineColor(kGray), RooFit.LineStyle(3),RooFit.Name("#alpha: jer dn") );


            paras = RooArgList();
	    ### Make a list of paramters as a function of the model after decorrelation
            if mlvj_model=="ErfExp_v1" or mlvj_model=="ErfPow_v1" or mlvj_model=="2Exp" :
             paras.add(self.workspace4fit_.var("Deco%s_sim_%s_%s%s_eig0"%(label,self.channel, self.wtagger_label, mass_spectrum) ));
             paras.add(self.workspace4fit_.var("Deco%s_sim_%s_%s%s_eig1"%(label,self.channel, self.wtagger_label, mass_spectrum) ));
             paras.add(self.workspace4fit_.var("Deco%s_sim_%s_%s%s_eig2"%(label,self.channel, self.wtagger_label, mass_spectrum) ));
             paras.add(self.workspace4fit_.var("Deco%s_sim_%s_%s%s_eig3"%(label,self.channel, self.wtagger_label, mass_spectrum) ));
             paras.add(self.workspace4fit_.var("Deco%s_sim_%s_%s%s_eig4"%(label,self.channel, self.wtagger_label, mass_spectrum) ));
             paras.add(self.workspace4fit_.var("Deco%s_sim_%s_%s%s_eig5"%(label,self.channel, self.wtagger_label, mass_spectrum) ));

            if mlvj_model=="ErfPow2_v1" or mlvj_model=="ErfPowExp_v1" :
             paras.add(self.workspace4fit_.var("Deco%s_sim_%s_%s%s_eig0"%(label,self.channel, self.wtagger_label, mass_spectrum) ));
             paras.add(self.workspace4fit_.var("Deco%s_sim_%s_%s%s_eig1"%(label,self.channel, self.wtagger_label, mass_spectrum) ));
             paras.add(self.workspace4fit_.var("Deco%s_sim_%s_%s%s_eig2"%(label,self.channel, self.wtagger_label, mass_spectrum) ));
             paras.add(self.workspace4fit_.var("Deco%s_sim_%s_%s%s_eig3"%(label,self.channel, self.wtagger_label, mass_spectrum) ));
             paras.add(self.workspace4fit_.var("Deco%s_sim_%s_%s%s_eig4"%(label,self.channel, self.wtagger_label, mass_spectrum) ));
             paras.add(self.workspace4fit_.var("Deco%s_sim_%s_%s%s_eig5"%(label,self.channel, self.wtagger_label, mass_spectrum) ));
             paras.add(self.workspace4fit_.var("Deco%s_sim_%s_%s%s_eig6"%(label,self.channel, self.wtagger_label, mass_spectrum) ));
             paras.add(self.workspace4fit_.var("Deco%s_sim_%s_%s%s_eig7"%(label,self.channel, self.wtagger_label, mass_spectrum) ));

            if mlvj_model=="Exp" or mlvj_model=="Pow":
             paras.add(self.workspace4fit_.var("Deco%s_sim_%s_%s%s_eig0"%(label,self.channel, self.wtagger_label, mass_spectrum) ));
             paras.add(self.workspace4fit_.var("Deco%s_sim_%s_%s%s_eig1"%(label,self.channel, self.wtagger_label, mass_spectrum) ));

            if mlvj_model=="ExpN" or mlvj_model=="ExpTail" or mlvj_model=="Pow2":
             paras.add(self.workspace4fit_.var("Deco%s_sim_%s_%s_mlvj_eig0%s"%(label,self.channel, self.wtagger_label, mass_spectrum) ));
             paras.add(self.workspace4fit_.var("Deco%s_sim_%s_%s_mlvj_eig1%s"%(label,self.channel, self.wtagger_label, mass_spectrum) ));
             paras.add(self.workspace4fit_.var("Deco%s_sim_%s_%s_mlvj_eig2%s"%(label,self.channel, self.wtagger_label, mass_spectrum) ));
             paras.add(self.workspace4fit_.var("Deco%s_sim_%s_%s_mlvj_eig3%s"%(label,self.channel, self.wtagger_label, mass_spectrum) ));

            if label == "_WJets0" or label == "_WJets1": ### draw error band ar 1 and 2 sigma using the decorrelated shape
             draw_error_band_shape_Decor("correct_factor_pdf_Deco%s_sim_%s_%s"%(label,self.channel, self.wtagger_label+mass_spectrum),"rrv_mass_lvj", paras, self.workspace4fit_,1 ,mplot,kGray+3,"F",3001,"#alpha #pm",20,400);
             draw_error_band_shape_Decor("correct_factor_pdf_Deco%s_sim_%s_%s"%(label,self.channel, self.wtagger_label+mass_spectrum),"rrv_mass_lvj", paras, self.workspace4fit_,2 ,mplot,kGreen+2,"F",3002,"#alpha #pm",20,400);
             draw_error_band_shape_Decor("correct_factor_pdf_Deco%s_sim_%s_%s"%(label,self.channel, self.wtagger_label+mass_spectrum),"rrv_mass_lvj", paras, self.workspace4fit_,1 ,mplot,kGray+3,"F",3001,"#alpha_invisible #pm",20,400);

            ### plot on the same canvas
            correct_factor_pdf_deco.plotOn(mplot, RooFit.LineColor(kBlack),RooFit.Name("#alpha_invisible") );

            if label == "_WJets0" : ## add also the plot of alternate ps and function on the canvas
             if self.workspace4fit_.pdf("correct_factor_pdf_Deco_WJets1_sim_%s_%s"%(self.channel,self.wtagger_label+mass_spectrum)):
                self.workspace4fit_.pdf("correct_factor_pdf_Deco_WJets1_sim_%s_%s"%(self.channel,self.wtagger_label+mass_spectrum)).plotOn(mplot, RooFit.LineColor(kMagenta), RooFit.LineStyle(3),RooFit.Name("#alpha_invisible: Alternate PS") );
             if self.workspace4fit_.pdf("correct_factor_pdf_Deco_WJets01_sim_%s_%s"%(self.channel,self.wtagger_label+mass_spectrum)):
                self.workspace4fit_.pdf("correct_factor_pdf_Deco_WJets01_sim_%s_%s"%(self.channel,self.wtagger_label+mass_spectrum)).plotOn(mplot, RooFit.LineColor(kOrange), RooFit.LineStyle(7),RooFit.Name("#alpha_invisible: Alternate Function") );

            ### Add the legend
            self.leg = self.legend4Plot(mplot,1,0, -0.0, -0.07, 0.02, 0.01, 0.);
            mplot.addObject(self.leg);

            ## set the Y axis in arbitrary unit
            if self.higgs_sample == "ggH600" or self.higgs_sample == "ggH700": tmp_y_max=0.25
            else: tmp_y_max=0.28
            mplot.GetYaxis().SetRangeUser(0.,tmp_y_max);

            #### Draw another axis with the real value of alpha
            model_pdf_sb_lo_WJets.getVal(RooArgSet(rrv_x)),
            model_pdf_signal_region_WJets.getVal(RooArgSet(rrv_x)),
            correct_factor_pdf_deco.getVal(RooArgSet(rrv_x)),
            tmp_alpha_ratio = ( model_pdf_signal_region_WJets.getVal(RooArgSet(rrv_x))/model_pdf_sb_lo_WJets.getVal(RooArgSet(rrv_x)) );
            tmp_alpha_pdf   = correct_factor_pdf_deco.getVal(RooArgSet(rrv_x)) * mplot.getFitRangeBinW(); ## value of the pdf in each point
            tmp_alpha_scale = tmp_alpha_ratio/tmp_alpha_pdf;

            #add alpha scale axis
            axis_alpha = TGaxis( rrv_x.getMax(), 0, rrv_x.getMax(), tmp_y_max, 0, tmp_y_max*tmp_alpha_scale, 510, "+L");
            axis_alpha.SetTitle("#alpha");
            axis_alpha.SetTitleOffset(0.65);
            axis_alpha.SetTitleSize(0.05);
            axis_alpha.SetLabelSize(0.045);
            axis_alpha.SetTitleFont(42);
            axis_alpha.SetLabelFont(42);
            mplot.addObject(axis_alpha);

            if mass_spectrum=="_mlvj_relaxed":
             self.draw_canvas(mplot,"plots_%s_%s_%s_%s_g1/other_relaxed/"%(options.additioninformation, self.channel,self.PS_model,self.wtagger_label),"correction_pdf%s_%s_%s_M_lvj_signal_region_to_sideband"%(label,self.PS_model,mlvj_model),0,1);
            else:
             self.draw_canvas(mplot,"plots_%s_%s_%s_%s_g1/other/"%(options.additioninformation, self.channel,self.PS_model,self.wtagger_label),"correction_pdf%s_%s_%s_M_lvj_signal_region_to_sideband"%(label,self.PS_model,mlvj_model),0,1);

        correct_factor_pdf_deco.getParameters(rdataset_WJets_sb_lo_mlvj).Print("v");
        self.workspace4fit_.Print();

        model_pdf_WJets_sb_lo_from_fitting_mlvj_Deco = self.workspace4fit_.pdf("model_pdf%s_sb_lo_from_fitting_%s_Deco%s_sb_lo_from_fitting_%s_%s"%(label,self.channel+mass_spectrum,label, self.channel,self.wtagger_label+mass_spectrum));           
        model_pdf_WJets_sb_lo_from_fitting_mlvj_Deco.Print("v");
    
        ### Wjets shape in the SR correctedfunction * sb
        model_pdf_WJets_signal_region_after_correct_mlvj = RooProdPdf("model_pdf%s_signal_region_%s_after_correct%s"%(label,self.channel,mass_spectrum),"model_pdf%s_signal_region_%s_after_correct%s"%(label,self.channel,mass_spectrum),model_pdf_WJets_sb_lo_from_fitting_mlvj_Deco,self.workspace4fit_.pdf("correct_factor_pdf_Deco%s_sim_%s_%s"%(label,self.channel,self.wtagger_label+mass_spectrum)));
        model_pdf_WJets_signal_region_after_correct_mlvj.Print()
        ### fix the parmaters and import in the workspace
        getattr(self.workspace4fit_,"import")(model_pdf_WJets_signal_region_after_correct_mlvj);

        ##### calculate the normalization and alpha for limit datacard
        self.workspace4fit_.var("rrv_number%s_signal_region_%s"%(label,self.channel+mass_spectrum)).Print();
        self.workspace4fit_.var("rrv_number%s_in_mj_signal_region_from_fitting_%s"%(label,self.channel)).Print();
        self.workspace4fit_.var("rrv_number%s_signal_region_%s"%(label,self.channel+mass_spectrum)).setVal(self.workspace4fit_.var("rrv_number%s_in_mj_signal_region_from_fitting_%s"%(label,self.channel)).getVal());
        self.workspace4fit_.var("rrv_number%s_signal_region_%s"%(label,self.channel+mass_spectrum)).setError(self.workspace4fit_.var("rrv_number%s_in_mj_signal_region_from_fitting_%s"%(label,self.channel)).getError());

        self.workspace4fit_.var("rrv_number%s_signal_region_%s"%(label,self.channel+mass_spectrum)).setConstant(kTRUE);

    ##### Method used to cycle on the events and for the dataset to be fitted

    def get_mj_and_mlvj_dataset(self,in_file_name, label, jet_mass="jet_mass_pr"):# to get the shape of m_lvj

        # read in tree
        fileIn_name = TString(self.file_Directory+in_file_name);
        fileIn = TFile(fileIn_name.Data());
        treeIn = fileIn.Get("otree");

        rrv_mass_j = self.workspace4fit_.var("rrv_mass_j") 
        rrv_mass_lvj = self.workspace4fit_.var("rrv_mass_lvj")

        rrv_weight = RooRealVar("rrv_weight","rrv_weight",0. ,10000000.) 
        
        # dataset of m_j -> before and after vbf cuts -> central object value
        rdataset_mj     = RooDataSet("rdataset"+label+"_"+self.channel+"_mj","rdataset"+label+"_"+self.channel+"_mj",RooArgSet(rrv_mass_j,rrv_weight),RooFit.WeightVar(rrv_weight) );
        rdataset4fit_mj = RooDataSet("rdataset4fit"+label+"_"+self.channel+"_mj","rdataset4fit"+label+"_"+self.channel+"_mj",RooArgSet(rrv_mass_j,rrv_weight),RooFit.WeightVar(rrv_weight) );

        #dataset of m_lvj -> before and after vbf cuts -> central object value
        rdataset_sb_lo_mlvj     = RooDataSet("rdataset"+label+"_sb_lo"+"_"+self.channel+"_mlvj","rdataset"+label+"_sb_lo"+"_"+self.channel+"_mlvj",RooArgSet(rrv_mass_lvj,rrv_weight),RooFit.WeightVar(rrv_weight) ); 
        rdataset_signal_region_mlvj = RooDataSet("rdataset"+label+"_signal_region"+"_"+self.channel+"_mlvj","rdataset"+label+"_signal_region"+"_"+self.channel+"_mlvj",RooArgSet(rrv_mass_lvj,rrv_weight),RooFit.WeightVar(rrv_weight) ); 
        rdataset_sb_hi_mlvj         = RooDataSet("rdataset"+label+"_sb_hi"+"_"+self.channel+"_mlvj","rdataset"+label+"_sb_hi"+"_"+self.channel+"_mlvj",RooArgSet(rrv_mass_lvj,rrv_weight),RooFit.WeightVar(rrv_weight) ); 

        rdataset4fit_sb_lo_mlvj     = RooDataSet("rdataset4fit"+label+"_sb_lo"+"_"+self.channel+"_mlvj","rdataset4fit"+label+"_sb_lo"+"_"+self.channel+"_mlvj",RooArgSet(rrv_mass_lvj,rrv_weight),RooFit.WeightVar(rrv_weight) ); 
        rdataset4fit_signal_region_mlvj = RooDataSet("rdataset4fit"+label+"_signal_region"+"_"+self.channel+"_mlvj","rdataset4fit"+label+"_signal_region"+"_"+self.channel+"_mlvj",RooArgSet(rrv_mass_lvj,rrv_weight),RooFit.WeightVar(rrv_weight) ); 
        rdataset4fit_sb_hi_mlvj     = RooDataSet("rdataset4fit"+label+"_sb_hi"+"_"+self.channel+"_mlvj","rdataset4fit"+label+"_sb_hi"+"_"+self.channel+"_mlvj",RooArgSet(rrv_mass_lvj,rrv_weight),RooFit.WeightVar(rrv_weight) ); 

        #dataset of jes_up
        rdataset_mj_jes_up  = RooDataSet("rdataset"+label+"massvbf_jes_up"+"_"+self.channel+"_mj","rdataset"+label+"massvbf_jes_up"+"_"+self.channel+"_mj",RooArgSet(rrv_mass_j,rrv_weight),RooFit.WeightVar(rrv_weight) );
        rdataset4fit_mj_jes_up = RooDataSet("rdataset4fit"+label+"massvbf_jes_up"+"_"+self.channel+"_mj","rdataset4fit"+label+"massvbf_jes_up"+"_"+self.channel+"_mj",RooArgSet(rrv_mass_j,rrv_weight),RooFit.WeightVar(rrv_weight) );
         
        rdataset_sb_lo_mlvj_jes_up         = RooDataSet("rdataset"+label+"massvbf_jes_up"+"_sb_lo"+"_"+self.channel+"_mlvj","rdataset"+label+"massvbf_jes_up"+"_sb_lo"+"_"+self.channel+"_mlvj",RooArgSet(rrv_mass_lvj,rrv_weight),RooFit.WeightVar(rrv_weight) ); 
        rdataset_signal_region_mlvj_jes_up = RooDataSet("rdataset"+label+"massvbf_jes_up"+"_signal_region"+"_"+self.channel+"_mlvj","rdataset"+label+"massvbf_jes_up"+"_signal_region"+"_"+self.channel+"_mlvj",RooArgSet(rrv_mass_lvj,rrv_weight),RooFit.WeightVar(rrv_weight) ); 
        rdataset_sb_hi_mlvj_jes_up         = RooDataSet("rdataset"+label+"massvbf_jes_up"+"_sb_hi"+"_"+self.channel+"_mlvj","rdataset"+label+"massvbf_jes_up"+"_sb_hi"+"_"+self.channel+"_mlvj",RooArgSet(rrv_mass_lvj,rrv_weight),RooFit.WeightVar(rrv_weight) ); 

        rdataset4fit_sb_lo_mlvj_jes_up  = RooDataSet("rdataset4fit"+label+"massvbf_jes_up"+"_sb_lo"+"_"+self.channel+"_mlvj","rdataset4fit"+label+"massvbf_jes_up"+"_sb_lo"+"_"+self.channel+"_mlvj",RooArgSet(rrv_mass_lvj,rrv_weight),RooFit.WeightVar(rrv_weight) ); 
        rdataset4fit_signal_region_mlvj_jes_up = RooDataSet("rdataset4fit"+label+"massvbf_jes_up"+"_signal_region"+"_"+self.channel+"_mlvj","rdataset4fit"+label+"massvbf_jes_up"+"_signal_region"+"_"+self.channel+"_mlvj",RooArgSet(rrv_mass_lvj,rrv_weight),RooFit.WeightVar(rrv_weight) ); 
        rdataset4fit_sb_hi_mlvj_jes_up  = RooDataSet("rdataset4fit"+label+"massvbf_jes_up"+"_sb_hi"+"_"+self.channel+"_mlvj","rdataset4fit"+label+"massvbf_jes_up"+"_sb_hi"+"_"+self.channel+"_mlvj",RooArgSet(rrv_mass_lvj,rrv_weight),RooFit.WeightVar(rrv_weight) ); 

        #dataset of applying jes dn
        rdataset_mj_jes_dn  = RooDataSet("rdataset"+label+"massvbf_jes_dn"+"_"+self.channel+"_mj","rdataset"+label+"massvbf_jes_dn"+"_"+self.channel+"_mj",RooArgSet(rrv_mass_j,rrv_weight),RooFit.WeightVar(rrv_weight) );
        rdataset4fit_mj_jes_dn = RooDataSet("rdataset4fit"+label+"massvbf_jes_dn"+"_"+self.channel+"_mj","rdataset4fit"+label+"massvbf_jes_dn"+"_"+self.channel+"_mj",RooArgSet(rrv_mass_j,rrv_weight),RooFit.WeightVar(rrv_weight) );

        rdataset_sb_lo_mlvj_jes_dn         = RooDataSet("rdataset"+label+"massvbf_jes_dn"+"_sb_lo"+"_"+self.channel+"_mlvj","rdataset"+label+"massvbf_jes_dn"+"_sb_lo"+"_"+self.channel+"_mlvj",RooArgSet(rrv_mass_lvj,rrv_weight),RooFit.WeightVar(rrv_weight) ); 
        rdataset_signal_region_mlvj_jes_dn = RooDataSet("rdataset"+label+"massvbf_jes_dn"+"_signal_region"+"_"+self.channel+"_mlvj","rdataset"+label+"massvbf_jes_dn"+"_signal_region"+"_"+self.channel+"_mlvj",RooArgSet(rrv_mass_lvj,rrv_weight),RooFit.WeightVar(rrv_weight) ); 
        rdataset_sb_hi_mlvj_jes_dn         = RooDataSet("rdataset"+label+"massvbf_jes_dn"+"_sb_hi"+"_"+self.channel+"_mlvj","rdataset"+label+"massvbf_jes_dn"+"_sb_hi"+"_"+self.channel+"_mlvj",RooArgSet(rrv_mass_lvj,rrv_weight),RooFit.WeightVar(rrv_weight) ); 

        rdataset4fit_sb_lo_mlvj_jes_dn  = RooDataSet("rdataset4fit"+label+"massvbf_jes_dn"+"_sb_lo"+"_"+self.channel+"_mlvj","rdataset4fit"+label+"massvbf_jes_dn"+"_sb_lo"+"_"+self.channel+"_mlvj",RooArgSet(rrv_mass_lvj,rrv_weight),RooFit.WeightVar(rrv_weight) ); 
        rdataset4fit_signal_region_mlvj_jes_dn = RooDataSet("rdataset4fit"+label+"massvbf_jes_dn"+"_signal_region"+"_"+self.channel+"_mlvj","rdataset4fit"+label+"massvbf_jes_dn"+"_signal_region"+"_"+self.channel+"_mlvj",RooArgSet(rrv_mass_lvj,rrv_weight),RooFit.WeightVar(rrv_weight) ); 
        rdataset4fit_sb_hi_mlvj_jes_dn     = RooDataSet("rdataset4fit"+label+"massvbf_jes_dn"+"_sb_hi"+"_"+self.channel+"_mlvj","rdataset4fit"+label+"massvbf_jes_dn"+"_sb_hi"+"_"+self.channel+"_mlvj",RooArgSet(rrv_mass_lvj,rrv_weight),RooFit.WeightVar(rrv_weight) ); 


        #dataset of applying jer up
        rdataset_mj_jer_up  = RooDataSet("rdataset"+label+"massvbf_jer_up"+"_"+self.channel+"_mj","rdataset"+label+"massvbf_jer_up"+"_"+self.channel+"_mj",RooArgSet(rrv_mass_j,rrv_weight),RooFit.WeightVar(rrv_weight) );
        rdataset4fit_mj_jer_up = RooDataSet("rdataset4fit"+label+"massvbf_jer_up"+"_"+self.channel+"_mj","rdataset4fit"+label+"massvbf_jer_up"+"_"+self.channel+"_mj",RooArgSet(rrv_mass_j,rrv_weight),RooFit.WeightVar(rrv_weight) );

        rdataset_sb_lo_mlvj_jer_up         = RooDataSet("rdataset"+label+"massvbf_jer_up"+"_sb_lo"+"_"+self.channel+"_mlvj","rdataset"+label+"massvbf_jer_up"+"_sb_lo"+"_"+self.channel+"_mlvj",RooArgSet(rrv_mass_lvj,rrv_weight),RooFit.WeightVar(rrv_weight) ); 
        rdataset_signal_region_mlvj_jer_up = RooDataSet("rdataset"+label+"massvbf_jer_up"+"_signal_region"+"_"+self.channel+"_mlvj","rdataset"+label+"massvbf_jer_up"+"_signal_region"+"_"+self.channel+"_mlvj",RooArgSet(rrv_mass_lvj,rrv_weight),RooFit.WeightVar(rrv_weight) ); 
        rdataset_sb_hi_mlvj_jer_up         = RooDataSet("rdataset"+label+"massvbf_jer_up"+"_sb_hi"+"_"+self.channel+"_mlvj","rdataset"+label+"massvbf_jer_up"+"_sb_hi"+"_"+self.channel+"_mlvj",RooArgSet(rrv_mass_lvj,rrv_weight),RooFit.WeightVar(rrv_weight) ); 

        rdataset4fit_sb_lo_mlvj_jer_up  = RooDataSet("rdataset4fit"+label+"massvbf_jer_up"+"_sb_lo"+"_"+self.channel+"_mlvj","rdataset4fit"+label+"massvbf_jer_up"+"_sb_lo"+"_"+self.channel+"_mlvj",RooArgSet(rrv_mass_lvj,rrv_weight),RooFit.WeightVar(rrv_weight) ); 
        rdataset4fit_signal_region_mlvj_jer_up = RooDataSet("rdataset4fit"+label+"massvbf_jer_up"+"_signal_region"+"_"+self.channel+"_mlvj","rdataset4fit"+label+"massvbf_jer_up"+"_signal_region"+"_"+self.channel+"_mlvj",RooArgSet(rrv_mass_lvj,rrv_weight),RooFit.WeightVar(rrv_weight) ); 
        rdataset4fit_sb_hi_mlvj_jer_up     = RooDataSet("rdataset4fit"+label+"massvbf_jer_up"+"_sb_hi"+"_"+self.channel+"_mlvj","rdataset4fit"+label+"massvbf_jer_up"+"_sb_hi"+"_"+self.channel+"_mlvj",RooArgSet(rrv_mass_lvj,rrv_weight),RooFit.WeightVar(rrv_weight) ); 

        #dataset of applying jer dn
        rdataset_mj_jer_dn  = RooDataSet("rdataset"+label+"massvbf_jer_dn"+"_"+self.channel+"_mj","rdataset"+label+"massvbf_jer_dn"+"_"+self.channel+"_mj",RooArgSet(rrv_mass_j,rrv_weight),RooFit.WeightVar(rrv_weight) );
        rdataset4fit_mj_jer_dn = RooDataSet("rdataset4fit"+label+"massvbf_jer_dn"+"_"+self.channel+"_mj","rdataset4fit"+label+"massvbf_jer_dn"+"_"+self.channel+"_mj",RooArgSet(rrv_mass_j,rrv_weight),RooFit.WeightVar(rrv_weight) );

        rdataset_sb_lo_mlvj_jer_dn         = RooDataSet("rdataset"+label+"massvbf_jer_dn"+"_sb_lo"+"_"+self.channel+"_mlvj","rdataset"+label+"massvbf_jer_dn"+"_sb_lo"+"_"+self.channel+"_mlvj",RooArgSet(rrv_mass_lvj,rrv_weight),RooFit.WeightVar(rrv_weight) ); 
        rdataset_signal_region_mlvj_jer_dn = RooDataSet("rdataset"+label+"massvbf_jer_dn"+"_signal_region"+"_"+self.channel+"_mlvj","rdataset"+label+"massvbf_jer_dn"+"_signal_region"+"_"+self.channel+"_mlvj",RooArgSet(rrv_mass_lvj,rrv_weight),RooFit.WeightVar(rrv_weight) ); 
        rdataset_sb_hi_mlvj_jer_dn         = RooDataSet("rdataset"+label+"massvbf_jer_dn"+"_sb_hi"+"_"+self.channel+"_mlvj","rdataset"+label+"massvbf_jer_dn"+"_sb_hi"+"_"+self.channel+"_mlvj",RooArgSet(rrv_mass_lvj,rrv_weight),RooFit.WeightVar(rrv_weight) ); 

        rdataset4fit_sb_lo_mlvj_jer_dn  = RooDataSet("rdataset4fit"+label+"massvbf_jer_dn"+"_sb_lo"+"_"+self.channel+"_mlvj","rdataset4fit"+label+"massvbf_jer_dn"+"_sb_lo"+"_"+self.channel+"_mlvj",RooArgSet(rrv_mass_lvj,rrv_weight),RooFit.WeightVar(rrv_weight) ); 
        rdataset4fit_signal_region_mlvj_jer_dn = RooDataSet("rdataset4fit"+label+"massvbf_jer_dn"+"_signal_region"+"_"+self.channel+"_mlvj","rdataset4fit"+label+"massvbf_jer_dn"+"_signal_region"+"_"+self.channel+"_mlvj",RooArgSet(rrv_mass_lvj,rrv_weight),RooFit.WeightVar(rrv_weight) ); 
        rdataset4fit_sb_hi_mlvj_jer_dn     = RooDataSet("rdataset4fit"+label+"massvbf_jer_dn"+"_sb_hi"+"_"+self.channel+"_mlvj","rdataset4fit"+label+"massvbf_jer_dn"+"_sb_hi"+"_"+self.channel+"_mlvj",RooArgSet(rrv_mass_lvj,rrv_weight),RooFit.WeightVar(rrv_weight) ); 


        #dataset of applying jer 
        rdataset_mj_jer  = RooDataSet("rdataset"+label+"massvbf_jer"+"_"+self.channel+"_mj","rdataset"+label+"massvbf_jer"+"_"+self.channel+"_mj",RooArgSet(rrv_mass_j,rrv_weight),RooFit.WeightVar(rrv_weight) );
        rdataset4fit_mj_jer = RooDataSet("rdataset4fit"+label+"massvbf_jer"+"_"+self.channel+"_mj","rdataset4fit"+label+"massvbf_jer"+"_"+self.channel+"_mj",RooArgSet(rrv_mass_j,rrv_weight),RooFit.WeightVar(rrv_weight) );

        rdataset_sb_lo_mlvj_jer         = RooDataSet("rdataset"+label+"massvbf_jer"+"_sb_lo"+"_"+self.channel+"_mlvj","rdataset"+label+"massvbf_jer"+"_sb_lo"+"_"+self.channel+"_mlvj",RooArgSet(rrv_mass_lvj,rrv_weight),RooFit.WeightVar(rrv_weight) ); 
        rdataset_signal_region_mlvj_jer = RooDataSet("rdataset"+label+"massvbf_jer"+"_signal_region"+"_"+self.channel+"_mlvj","rdataset"+label+"massvbf_jer"+"_signal_region"+"_"+self.channel+"_mlvj",RooArgSet(rrv_mass_lvj,rrv_weight),RooFit.WeightVar(rrv_weight) ); 
        rdataset_sb_hi_mlvj_jer         = RooDataSet("rdataset"+label+"massvbf_jer"+"_sb_hi"+"_"+self.channel+"_mlvj","rdataset"+label+"massvbf_jer"+"_sb_hi"+"_"+self.channel+"_mlvj",RooArgSet(rrv_mass_lvj,rrv_weight),RooFit.WeightVar(rrv_weight) ); 

        rdataset4fit_sb_lo_mlvj_jer  = RooDataSet("rdataset4fit"+label+"massvbf_jer"+"_sb_lo"+"_"+self.channel+"_mlvj","rdataset4fit"+label+"massvbf_jer"+"_sb_lo"+"_"+self.channel+"_mlvj",RooArgSet(rrv_mass_lvj,rrv_weight),RooFit.WeightVar(rrv_weight) ); 
        rdataset4fit_signal_region_mlvj_jer = RooDataSet("rdataset4fit"+label+"massvbf_jer"+"_signal_region"+"_"+self.channel+"_mlvj","rdataset4fit"+label+"massvbf_jer"+"_signal_region"+"_"+self.channel+"_mlvj",RooArgSet(rrv_mass_lvj,rrv_weight),RooFit.WeightVar(rrv_weight) ); 
        rdataset4fit_sb_hi_mlvj_jer     = RooDataSet("rdataset4fit"+label+"massvbf_jer"+"_sb_hi"+"_"+self.channel+"_mlvj","rdataset4fit"+label+"massvbf_jer"+"_sb_hi"+"_"+self.channel+"_mlvj",RooArgSet(rrv_mass_lvj,rrv_weight),RooFit.WeightVar(rrv_weight) ); 

        
        ###### Define the event categorization
        data_category = RooCategory("data_category","data_category");
        data_category.defineType("sideband");
        data_category.defineType("signal_region");

        combData = RooDataSet("combData"+label+"_"+self.channel,"combData"+label+"_"+self.channel,RooArgSet(rrv_mass_lvj, data_category, rrv_weight),RooFit.WeightVar(rrv_weight) );
        combData4fit = RooDataSet("combData4fit"+label+"_"+self.channel,"combData4fit"+label+"_"+self.channel,RooArgSet(rrv_mass_lvj, data_category, rrv_weight),RooFit.WeightVar(rrv_weight) );
        
        ## jes_up
        combData_jes_up = RooDataSet("combData"+label+"massvbf_jes_up"+"_"+self.channel,"combData"+label+"massvbf_jes_up"+"_"+self.channel,RooArgSet(rrv_mass_lvj, data_category, rrv_weight),RooFit.WeightVar(rrv_weight) );
        combData4fit_jes_up = RooDataSet("combData4fit"+label+"massvbf_jes_up"+"_"+self.channel,"combData4fit"+label+"massvbf_jes_up"+"_"+self.channel,RooArgSet(rrv_mass_lvj, data_category, rrv_weight),RooFit.WeightVar(rrv_weight) );

        ## jes_dn
        combData_jes_dn = RooDataSet("combData"+label+"massvbf_jes_dn"+"_"+self.channel,"combData"+label+"massvbf_jes_dn"+"_"+self.channel,RooArgSet(rrv_mass_lvj, data_category, rrv_weight),RooFit.WeightVar(rrv_weight) );
        combData4fit_jes_dn = RooDataSet("combData4fit"+label+"massvbf_jes_dn"+"_"+self.channel,"combData4fit"+label+"massvbf_jes_dn"+"_"+self.channel,RooArgSet(rrv_mass_lvj, data_category, rrv_weight),RooFit.WeightVar(rrv_weight) );

        ## jer_up
        combData_jer_up = RooDataSet("combData"+label+"massvbf_jer_up"+"_"+self.channel,"combData"+label+"massvbf_jer_up"+"_"+self.channel,RooArgSet(rrv_mass_lvj, data_category, rrv_weight),RooFit.WeightVar(rrv_weight) );
        combData4fit_jer_up = RooDataSet("combData4fit"+label+"massvbf_jer_up"+"_"+self.channel,"combData4fit"+label+"massvbf_jer_up"+"_"+self.channel,RooArgSet(rrv_mass_lvj, data_category, rrv_weight),RooFit.WeightVar(rrv_weight) );

        ## jer_dn
        combData_jer_dn = RooDataSet("combData"+label+"massvbf_jer_dn"+"_"+self.channel,"combData"+label+"massvbf_jer_dn"+"_"+self.channel,RooArgSet(rrv_mass_lvj, data_category, rrv_weight),RooFit.WeightVar(rrv_weight) );
        combData4fit_jer_dn = RooDataSet("combData4fit"+label+"massvbf_jer_dn"+"_"+self.channel,"combData4fit"+label+"massvbf_jer_dn"+"_"+self.channel,RooArgSet(rrv_mass_lvj, data_category, rrv_weight),RooFit.WeightVar(rrv_weight) );

        ## jer
        combData_jer = RooDataSet("combData"+label+"massvbf_jer"+"_"+self.channel,"combData"+label+"massvbf_jer"+"_"+self.channel,RooArgSet(rrv_mass_lvj, data_category, rrv_weight),RooFit.WeightVar(rrv_weight) );
        combData4fit_jer = RooDataSet("combData4fit"+label+"massvbf_jer"+"_"+self.channel,"combData4fit"+label+"massvbf_jer"+"_"+self.channel,RooArgSet(rrv_mass_lvj, data_category, rrv_weight),RooFit.WeightVar(rrv_weight) );
        
        print "N entries: ", treeIn.GetEntries();

        hnum_4region = TH1D("hnum_4region"+label+"_"+self.channel,"hnum_4region"+label+"_"+self.channel,4,-1.5,2.5);# m_j   -1: sb_lo; 0:signal_region; 1: sb_hi; 2:total        
        hnum_2region = TH1D("hnum_2region"+label+"_"+self.channel,"hnum_2region"+label+"_"+self.channel,2,-0.5,1.5);# m_lvj  0: signal_region; 1: total
        
        hnum_4region_jes_up = TH1D("hnum_4region"+label+"massvbf_jes_up"+"_"+self.channel,"hnum_4region"+label+"massvbf_jes_up"+"_"+self.channel,4,-1.5,2.5);  
        hnum_2region_jes_up = TH1D("hnum_2region"+label+"massvbf_jes_up"+"_"+self.channel,"hnum_2region"+label+"massvbf_jes_up"+"_"+self.channel,2,-0.5,1.5);

        hnum_4region_jes_dn = TH1D("hnum_4region"+label+"massvbf_jes_dn"+"_"+self.channel,"hnum_4region"+label+"massvbf_jes_dn"+"_"+self.channel,4,-1.5,2.5);  
        hnum_2region_jes_dn = TH1D("hnum_2region"+label+"massvbf_jes_dn"+"_"+self.channel,"hnum_2region"+label+"massvbf_jes_dn"+"_"+self.channel,2,-0.5,1.5);

        hnum_4region_jer_up = TH1D("hnum_4region"+label+"massvbf_jer_up"+"_"+self.channel,"hnum_4region"+label+"massvbf_jer_up"+"_"+self.channel,4,-1.5,2.5);  
        hnum_2region_jer_up = TH1D("hnum_2region"+label+"massvbf_jer_up"+"_"+self.channel,"hnum_2region"+label+"massvbf_jer_up"+"_"+self.channel,2,-0.5,1.5);

        hnum_4region_jer_dn = TH1D("hnum_4region"+label+"massvbf_jer_dn"+"_"+self.channel,"hnum_4region"+label+"massvbf_jer_dn"+"_"+self.channel,4,-1.5,2.5);  
        hnum_2region_jer_dn = TH1D("hnum_2region"+label+"massvbf_jer_dn"+"_"+self.channel,"hnum_2region"+label+"massvbf_jer_dn"+"_"+self.channel,2,-0.5,1.5);

        hnum_4region_jer = TH1D("hnum_4region"+label+"massvbf_jer"+"_"+self.channel,"hnum_4region"+label+"massvbf_jer"+"_"+self.channel,4,-1.5,2.5);  
        hnum_2region_jer = TH1D("hnum_2region"+label+"massvbf_jer"+"_"+self.channel,"hnum_2region"+label+"massvbf_jer"+"_"+self.channel,2,-0.5,1.5);
        

        tmp_scale_to_lumi = 0 ;

        for i in range(treeIn.GetEntries()):


          if i % 10000 == 0: print "iEvent: ",i
          treeIn.GetEntry(i);

          discriminantCut = False;

          wtagger=-1;
          wtagger=getattr(treeIn,"jet_tau2tau1");

          if wtagger < self.wtagger_cut:
            discriminantCut = True;
          else:
            discriminantCut = False;
        
          tmp_scale_to_lumi = treeIn.wSampleWeight;
                                
          jet_1 = ROOT.TLorentzVector();
          jet_2 = ROOT.TLorentzVector();

          njet = 0. ; tmp_vbf_dEta =0.; tmp_vbf_Mjj = 0.; ungroomed_jet_pt = 0.; pfMET = 0.; mass_lvj = 0. ;

          # jet mass , central value
          tmp_jet_mass = getattr(treeIn, jet_mass);
          tmp_vbf_dEta = math.fabs(getattr(treeIn, "vbf_maxpt_j1_eta")-getattr(treeIn,"vbf_maxpt_j2_eta"));
          tmp_vbf_Mjj  = getattr(treeIn, "vbf_maxpt_jj_m");
          njet         = getattr(treeIn,"numberJetBin");
          ungroomed_jet_pt = getattr(treeIn,"ungroomed_jet_pt");
          pfMET    = getattr(treeIn,"pfMET");
          mass_lvj = getattr(treeIn,"mass_lvj_type0_met");

          
          # jet mass jes_up
          tmp_jet_mass_jes_up = getattr(treeIn, "jet_mass_pr_jes_up");
          tmp_vbf_dEta_jes_up = math.fabs(getattr(treeIn, "vbf_maxpt_j1_eta_jes_up")-getattr(treeIn,"vbf_maxpt_j2_eta_jes_up"));
          jet_1.SetPtEtaPhiM(getattr(treeIn,"vbf_maxpt_j1_pt_jes_up"),getattr(treeIn,"vbf_maxpt_j1_eta_jes_up"),getattr(treeIn,"vbf_maxpt_j1_phi_jes_up"),getattr(treeIn,"vbf_maxpt_j1_m_jes_up"));
          jet_2.SetPtEtaPhiM(getattr(treeIn,"vbf_maxpt_j2_pt_jes_up"),getattr(treeIn,"vbf_maxpt_j2_eta_jes_up"),getattr(treeIn,"vbf_maxpt_j2_phi_jes_up"),getattr(treeIn,"vbf_maxpt_j2_m_jes_up"));
          tmp_vbf_Mjj_jes_up      = (jet_1+jet_2).M();
          ungroomed_jet_pt_jes_up = getattr(treeIn,"ungroomed_jet_pt_jes_up");
          njet_jes_up = 0 ;
          if(getattr(treeIn,"vbf_maxpt_j1_pt_jes_up") > 30.):
               njet_jes_up = njet_jes_up +1 ;
          if(getattr(treeIn,"vbf_maxpt_j2_pt_jes_up") > 30.):
               njet_jes_up = njet_jes_up +1 ;
          pfMET_jes_up = getattr(treeIn,"pfMET_jes_up");
          mass_lvj_jes_up = getattr(treeIn,"mass_lvj_type0_met_jes_up");

          # jet mass jes_dn
          tmp_jet_mass_jes_dn = getattr(treeIn, "jet_mass_pr_jes_dn");
          tmp_vbf_dEta_jes_dn = math.fabs(getattr(treeIn, "vbf_maxpt_j1_eta_jes_dn")-getattr(treeIn,"vbf_maxpt_j2_eta_jes_dn"));
          jet_1.SetPtEtaPhiM(getattr(treeIn,"vbf_maxpt_j1_pt_jes_dn"),getattr(treeIn,"vbf_maxpt_j1_eta_jes_dn"),getattr(treeIn,"vbf_maxpt_j1_phi_jes_dn"),getattr(treeIn,"vbf_maxpt_j1_m_jes_dn"));
          jet_2.SetPtEtaPhiM(getattr(treeIn,"vbf_maxpt_j2_pt_jes_dn"),getattr(treeIn,"vbf_maxpt_j2_eta_jes_dn"),getattr(treeIn,"vbf_maxpt_j2_phi_jes_dn"),getattr(treeIn,"vbf_maxpt_j2_m_jes_dn"));
          tmp_vbf_Mjj_jes_dn = (jet_1 + jet_2).M();
          ungroomed_jet_pt_jes_dn = getattr(treeIn,"ungroomed_jet_pt_jes_dn");
          njet_jes_dn = 0 ;
          if(getattr(treeIn,"vbf_maxpt_j1_pt_jes_dn") > 30.):
               njet_jes_dn = njet_jes_dn +1 ;
          if(getattr(treeIn,"vbf_maxpt_j2_pt_jes_dn") > 30.):
               njet_jes_dn = njet_jes_dn +1 ;
          pfMET_jes_dn = getattr(treeIn,"pfMET_jes_dn");
          mass_lvj_jes_dn = getattr(treeIn,"mass_lvj_type0_met_jes_dn");

          #jet mass jer
          tmp_jet_mass_jer = getattr(treeIn, "jet_mass_pr_jer");
          tmp_vbf_dEta_jer = math.fabs(getattr(treeIn, "vbf_maxpt_j1_eta_jer")-getattr(treeIn,"vbf_maxpt_j2_eta_jer"));
          jet_1.SetPtEtaPhiM(getattr(treeIn,"vbf_maxpt_j1_pt_jer"),getattr(treeIn,"vbf_maxpt_j1_eta_jer"),getattr(treeIn,"vbf_maxpt_j1_phi_jer"),getattr(treeIn,"vbf_maxpt_j1_m_jer"));
          jet_2.SetPtEtaPhiM(getattr(treeIn,"vbf_maxpt_j2_pt_jer"),getattr(treeIn,"vbf_maxpt_j2_eta_jer"),getattr(treeIn,"vbf_maxpt_j2_phi_jer"),getattr(treeIn,"vbf_maxpt_j2_m_jer"));
          tmp_vbf_Mjj_jer = (jet_1+jet_2).M();
          ungroomed_jet_pt_jer = getattr(treeIn,"ungroomed_jet_pt_jer");
          njet_jer = 0 ;
          if(getattr(treeIn,"vbf_maxpt_j1_pt_jer") > 30.):
               njet_jer = njet_jer +1 ;
          if(getattr(treeIn,"vbf_maxpt_j2_pt_jer") > 30.):
               njet_jer = njet_jer +1 ;
          pfMET_jer = getattr(treeIn,"pfMET_jer");
          mass_lvj_jer = getattr(treeIn,"mass_lvj_type0_met_jer");

          #jet mass jer up
          tmp_jet_mass_jer_up = getattr(treeIn, "jet_mass_pr_jer_up");
          tmp_vbf_dEta_jer_up = math.fabs(getattr(treeIn, "vbf_maxpt_j1_eta_jer_up")-getattr(treeIn,"vbf_maxpt_j2_eta_jer_up"));
          jet_1.SetPtEtaPhiM(getattr(treeIn,"vbf_maxpt_j1_pt_jer_up"),getattr(treeIn,"vbf_maxpt_j1_eta_jer_up"),getattr(treeIn,"vbf_maxpt_j1_phi_jer_up"),getattr(treeIn,"vbf_maxpt_j1_m_jer_up"));
          jet_2.SetPtEtaPhiM(getattr(treeIn,"vbf_maxpt_j2_pt_jer_up"),getattr(treeIn,"vbf_maxpt_j2_eta_jer_up"),getattr(treeIn,"vbf_maxpt_j2_phi_jer_up"),getattr(treeIn,"vbf_maxpt_j2_m_jer_up"));
          tmp_vbf_Mjj_jer_up = (jet_1+jet_2).M();
          ungroomed_jet_pt_jer_up = getattr(treeIn,"ungroomed_jet_pt_jer_up");
          njet_jer_up = 0;
          if(getattr(treeIn,"vbf_maxpt_j1_pt_jer_up") > 30.):
               njet_jer_up = njet_jer_up +1 ;
          if(getattr(treeIn,"vbf_maxpt_j2_pt_jer_up") > 30.):
               njet_jer_up = njet_jer_up +1 ;
          pfMET_jer_up = getattr(treeIn,"pfMET_jer_up");
          mass_lvj_jer_up = getattr(treeIn,"mass_lvj_type0_met_jer_up");

          #jet mass jer dn
          tmp_jet_mass_jer_dn = getattr(treeIn, "jet_mass_pr_jer_dn");
          tmp_vbf_dEta_jer_dn = math.fabs(getattr(treeIn, "vbf_maxpt_j1_eta_jer_dn")-getattr(treeIn,"vbf_maxpt_j2_eta_jer_dn"));
          jet_1.SetPtEtaPhiM(getattr(treeIn,"vbf_maxpt_j1_pt_jer_dn"),getattr(treeIn,"vbf_maxpt_j1_eta_jer_dn"),getattr(treeIn,"vbf_maxpt_j1_phi_jer_dn"),getattr(treeIn,"vbf_maxpt_j1_m_jer_dn"));
          jet_2.SetPtEtaPhiM(getattr(treeIn,"vbf_maxpt_j2_pt_jer_dn"),getattr(treeIn,"vbf_maxpt_j2_eta_jer_dn"),getattr(treeIn,"vbf_maxpt_j2_phi_jer_dn"),getattr(treeIn,"vbf_maxpt_j2_m_jer_dn"));
          tmp_vbf_Mjj_jer_dn = (jet_1 + jet_2).M();
          ungroomed_jet_pt_jer_dn = getattr(treeIn,"ungroomed_jet_pt_jer_dn");
          njet_jer_dn = 0 ;
          if(getattr(treeIn,"vbf_maxpt_j1_pt_jer_dn") > 30.):
               njet_jer_dn = njet_jer_dn +1 ;
          if(getattr(treeIn,"vbf_maxpt_j2_pt_jer_dn") > 30.):
               njet_jer_dn = njet_jer_dn +1 ;
          pfMET_jer_dn = getattr(treeIn,"pfMET_jer_dn");
          mass_lvj_jer_dn = getattr(treeIn,"mass_lvj_type0_met_jer_dn");
          
          isFullVBF = 0 ;
          isFullVBF_jes_up = 0;
          isFullVBF_jes_dn = 0;
          isFullVBF_jer = 0;
          isFullVBF_jer_up = 0;
          isFullVBF_jer_dn = 0;
          
          if ungroomed_jet_pt > 200. and discriminantCut and tmp_jet_mass >= rrv_mass_j.getMin() and tmp_jet_mass<=rrv_mass_j.getMax() and getattr(treeIn,"vbf_maxpt_j1_bDiscriminatorCSV") < 0.679 and getattr(treeIn,"vbf_maxpt_j2_bDiscriminatorCSV")<0.679 and mass_lvj >= rrv_mass_lvj.getMin() and mass_lvj <=rrv_mass_lvj.getMax() and getattr(treeIn,"v_pt") > self.vpt_cut and pfMET > self.pfMET_cut and getattr(treeIn,"l_pt") > self.lpt_cut and getattr(treeIn,"issignal")==1 and getattr(treeIn,"mass_ungroomedjet_closerjet") > self.top_veto_had and getattr(treeIn,"mass_leptonic_closerjet") > self.top_veto_lep and njet >=2 and tmp_vbf_dEta > self.dEta_cut and tmp_vbf_Mjj > self.Mjj_cut:
            isFullVBF = 2 ;
          
          if ungroomed_jet_pt_jes_up > 200. and discriminantCut and tmp_jet_mass_jes_up >= rrv_mass_j.getMin() and tmp_jet_mass_jes_up<=rrv_mass_j.getMax() and getattr(treeIn,"vbf_maxpt_j1_bDiscriminatorCSV") < 0.679 and getattr(treeIn,"vbf_maxpt_j2_bDiscriminatorCSV")<0.679 and mass_lvj_jes_up >= rrv_mass_lvj.getMin() and mass_lvj_jes_up <=rrv_mass_lvj.getMax() and getattr(treeIn,"v_pt") > self.vpt_cut and pfMET_jes_up > self.pfMET_cut and getattr(treeIn,"l_pt") > self.lpt_cut and getattr(treeIn,"issignal")==1 and getattr(treeIn,"mass_ungroomedjet_closerjet") > self.top_veto_had and getattr(treeIn,"mass_leptonic_closerjet") > self.top_veto_lep and njet_jes_up >=2 and tmp_vbf_dEta_jes_up > self.dEta_cut and tmp_vbf_Mjj_jes_up > self.Mjj_cut :
           isFullVBF_jes_up = 2 ;


          if ungroomed_jet_pt_jes_dn > 200. and discriminantCut and tmp_jet_mass_jes_dn >= rrv_mass_j.getMin() and tmp_jet_mass_jes_dn<=rrv_mass_j.getMax() and getattr(treeIn,"vbf_maxpt_j1_bDiscriminatorCSV") < 0.679 and getattr(treeIn,"vbf_maxpt_j2_bDiscriminatorCSV")<0.679 and mass_lvj_jes_dn >= rrv_mass_lvj.getMin() and mass_lvj_jes_dn <=rrv_mass_lvj.getMax() and getattr(treeIn,"v_pt") > self.vpt_cut and pfMET_jes_dn > self.pfMET_cut and getattr(treeIn,"l_pt") > self.lpt_cut and getattr(treeIn,"issignal")==1 and getattr(treeIn,"mass_ungroomedjet_closerjet") > self.top_veto_had and getattr(treeIn,"mass_leptonic_closerjet") > self.top_veto_lep and njet_jes_dn >=2 and tmp_vbf_dEta_jes_dn > self.dEta_cut and tmp_vbf_Mjj_jes_dn > self.Mjj_cut:
           isFullVBF_jes_dn = 2 ;

          if ungroomed_jet_pt_jer > 200. and discriminantCut and tmp_jet_mass_jer >= rrv_mass_j.getMin() and tmp_jet_mass_jer<=rrv_mass_j.getMax() and getattr(treeIn,"vbf_maxpt_j1_bDiscriminatorCSV") < 0.679 and getattr(treeIn,"vbf_maxpt_j2_bDiscriminatorCSV")<0.679 and mass_lvj_jer >= rrv_mass_lvj.getMin() and mass_lvj_jer <=rrv_mass_lvj.getMax() and getattr(treeIn,"v_pt") > self.vpt_cut and pfMET_jer > self.pfMET_cut and getattr(treeIn,"l_pt") > self.lpt_cut and getattr(treeIn,"issignal")==1 and getattr(treeIn,"mass_ungroomedjet_closerjet") > self.top_veto_had and getattr(treeIn,"mass_leptonic_closerjet") > self.top_veto_lep and njet_jer >=2 and tmp_vbf_dEta_jer > self.dEta_cut and tmp_vbf_Mjj_jer > self.Mjj_cut:          
           isFullVBF_jer = 2;

          if ungroomed_jet_pt_jer_up > 200. and discriminantCut and tmp_jet_mass_jer_up >= rrv_mass_j.getMin() and tmp_jet_mass_jer_up<=rrv_mass_j.getMax() and getattr(treeIn,"vbf_maxpt_j1_bDiscriminatorCSV") < 0.679 and getattr(treeIn,"vbf_maxpt_j2_bDiscriminatorCSV")<0.679 and mass_lvj_jer_up >= rrv_mass_lvj.getMin() and mass_lvj_jer_up <=rrv_mass_lvj.getMax() and getattr(treeIn,"v_pt") > self.vpt_cut and pfMET_jer_up > self.pfMET_cut and getattr(treeIn,"l_pt") > self.lpt_cut and getattr(treeIn,"issignal")==1 and getattr(treeIn,"mass_ungroomedjet_closerjet") > self.top_veto_had and getattr(treeIn,"mass_leptonic_closerjet") > self.top_veto_lep and njet_jer_up >=2 and tmp_vbf_dEta_jer_up > self.dEta_cut and tmp_vbf_Mjj_jer_up > self.Mjj_cut:          
           isFullVBF_jer_up = 2 ;

          if ungroomed_jet_pt_jer_dn > 200. and discriminantCut and tmp_jet_mass_jer_dn >= rrv_mass_j.getMin() and tmp_jet_mass_jer_dn<=rrv_mass_j.getMax() and getattr(treeIn,"vbf_maxpt_j1_bDiscriminatorCSV") < 0.679 and getattr(treeIn,"vbf_maxpt_j2_bDiscriminatorCSV")<0.679 and mass_lvj_jer_dn >= rrv_mass_lvj.getMin() and mass_lvj_jer_dn <=rrv_mass_lvj.getMax() and getattr(treeIn,"v_pt") > self.vpt_cut and pfMET_jer_dn > self.pfMET_cut and getattr(treeIn,"l_pt") > self.lpt_cut and getattr(treeIn,"issignal")==1 and getattr(treeIn,"mass_ungroomedjet_closerjet") > self.top_veto_had and getattr(treeIn,"mass_leptonic_closerjet") > self.top_veto_lep and njet_jer_dn >=2 and tmp_vbf_dEta_jer_dn > self.dEta_cut and tmp_vbf_Mjj_jer_dn > self.Mjj_cut:          
           isFullVBF_jer_dn = 2 ;
          
          if isFullVBF !=0 or isFullVBF_jes_up!=0 or isFullVBF_jes_dn!=0 or isFullVBF_jer!=0 or isFullVBF_jer_up!=0 or isFullVBF_jer_dn!=0 :
              
             tmp_event_weight = getattr(treeIn,"totalEventWeight");
             tmp_event_weight4fit = getattr(treeIn,"eff_and_pu_Weight");
             tmp_interference_weight_H600 = getattr(treeIn,"interference_Weight_H600");
             tmp_interference_weight_H700 = getattr(treeIn,"interference_Weight_H700");
             tmp_interference_weight_H800 = getattr(treeIn,"interference_Weight_H800");
             tmp_interference_weight_H900 = getattr(treeIn,"interference_Weight_H900");
             tmp_interference_weight_H1000 = getattr(treeIn,"interference_Weight_H1000");

             ## added by Nhan, getting additional BSM weight
             bsmWeightName = "bsmReweight_cPrime%02d_brNew%02d"%(options.cprime,options.BRnew);
             tmp_bsmWeight = getattr(treeIn, bsmWeightName);
             if tmp_bsmWeight < 0: tmp_bsmWeight = 1;
             
             if TString(label).Contains("ggH600"):
                tmp_event_weight = tmp_event_weight*tmp_interference_weight_H600
                tmp_event_weight4fit = tmp_event_weight4fit*tmp_interference_weight_H600
             if TString(label).Contains("ggH700"):
                tmp_event_weight = tmp_event_weight*tmp_interference_weight_H700
                tmp_event_weight4fit = tmp_event_weight4fit*tmp_interference_weight_H700
             if TString(label).Contains("ggH800"):
                tmp_event_weight = tmp_event_weight*tmp_interference_weight_H800
                tmp_event_weight4fit = tmp_event_weight4fit*tmp_interference_weight_H800
             if TString(label).Contains("ggH900"):
                tmp_event_weight = tmp_event_weight*tmp_interference_weight_H900
                tmp_event_weight4fit = tmp_event_weight4fit*tmp_interference_weight_H900
             if TString(label).Contains("ggH1000"):
                tmp_event_weight = tmp_event_weight*tmp_interference_weight_H1000
                tmp_event_weight4fit = tmp_event_weight4fit*tmp_interference_weight_H1000

             if TString(label).Contains("vbfH600"):
                tmp_event_weight = tmp_event_weight*treeIn.cps_Weight_H600;
                tmp_event_weight4fit = tmp_event_weight4fit*treeIn.cps_Weight_H600;
             if TString(label).Contains("vbfH700"):
                tmp_event_weight = tmp_event_weight*treeIn.cps_Weight_H700;
                tmp_event_weight4fit = tmp_event_weight4fit*treeIn.cps_Weight_H700;
             if TString(label).Contains("vbfH800"):
                tmp_event_weight = tmp_event_weight*treeIn.cps_Weight_H800;
                tmp_event_weight4fit = tmp_event_weight4fit*treeIn.cps_Weight_H800;
             if TString(label).Contains("vbfH900"):
                tmp_event_weight = tmp_event_weight*treeIn.cps_Weight_H900;
                tmp_event_weight4fit = tmp_event_weight4fit*treeIn.cps_Weight_H900;
             if TString(label).Contains("vbfH1000"):
                tmp_event_weight = tmp_event_weight*treeIn.cps_Weight_H1000;
                tmp_event_weight4fit = tmp_event_weight4fit*treeIn.cps_Weight_H1000;
 
             # for multi-sample, like STop and VV. There are two sample, and two wSampleWeight_value.Use the least wSampleWeight as scale.
             tmp_event_weight4fit = tmp_event_weight4fit*treeIn.wSampleWeight/tmp_scale_to_lumi;

             if TString(label).Contains("ggH") or TString(label).Contains("vbfH"):
                 tmp_event_weight = tmp_event_weight/self.higgs_xs_scale;
                 tmp_event_weight4fit = tmp_event_weight4fit/self.higgs_xs_scale;
                 ## added by Nhan
                 tmp_event_weight = tmp_event_weight*tmp_bsmWeight;
                 tmp_event_weight4fit=tmp_event_weight4fit*tmp_bsmWeight;

        
             if not label=="_data":
                     if TString(label).Contains("_TTbar") or TString(label).Contains("_STop") :
                         tmp_event_weight = tmp_event_weight*self.rrv_wtagger_eff_reweight_forT.getVal();
                     elif TString(label).Contains("_ggH") or TString(label).Contains("_vbfH") or TString(label).Contains("_VV") or TString(label).Contains("_WW_EWK") :
                         tmp_event_weight = tmp_event_weight*self.rrv_wtagger_eff_reweight_forV.getVal();

             tmp_event_weight        = tmp_event_weight* getattr(treeIn,"btag_weight"); ## add the btag weight 
             tmp_event_weight4fit    = tmp_event_weight4fit* getattr(treeIn,"btag_weight"); ## add the btag weight 

             ## central values
             rrv_mass_lvj.setVal(mass_lvj);
             rrv_mass_j.setVal(tmp_jet_mass);

             if tmp_jet_mass >= self.mj_sideband_lo_min and tmp_jet_mass < self.mj_sideband_lo_max and isFullVBF == 2:
                 rdataset_sb_lo_mlvj.add( RooArgSet( rrv_mass_lvj ), tmp_event_weight );
                 rdataset4fit_sb_lo_mlvj.add( RooArgSet( rrv_mass_lvj ), tmp_event_weight4fit );
                 data_category.setLabel("sideband");
                 combData.add(RooArgSet(rrv_mass_lvj,data_category),tmp_event_weight);
                 combData4fit.add(RooArgSet(rrv_mass_lvj,data_category),tmp_event_weight4fit);

             if tmp_jet_mass >= self.mj_signal_min and tmp_jet_mass < self.mj_signal_max and isFullVBF == 2:
                 rdataset_signal_region_mlvj.add( RooArgSet( rrv_mass_lvj ), tmp_event_weight );
                 rdataset4fit_signal_region_mlvj.add( RooArgSet( rrv_mass_lvj ), tmp_event_weight4fit );
                 data_category.setLabel("signal_region");
                 combData.add(RooArgSet(rrv_mass_lvj,data_category),tmp_event_weight);
                 combData4fit.add(RooArgSet(rrv_mass_lvj,data_category),tmp_event_weight4fit);
                 hnum_2region.Fill(1,tmp_event_weight);
                 if mass_lvj >=self.mlvj_signal_min and mass_lvj <self.mlvj_signal_max: 
                   hnum_2region.Fill(0,tmp_event_weight);

             if tmp_jet_mass >= self.mj_sideband_hi_min and tmp_jet_mass < self.mj_sideband_hi_max and isFullVBF == 2:
                 rdataset_sb_hi_mlvj.add( RooArgSet( rrv_mass_lvj ), tmp_event_weight );
                 rdataset4fit_sb_hi_mlvj.add( RooArgSet( rrv_mass_lvj ), tmp_event_weight4fit );

             if isFullVBF == 2: 
              rdataset_mj.add( RooArgSet( rrv_mass_j ), tmp_event_weight );
              rdataset4fit_mj.add( RooArgSet( rrv_mass_j ), tmp_event_weight4fit );
              if tmp_jet_mass >=self.mj_sideband_lo_min and tmp_jet_mass <self.mj_sideband_lo_max: 
                 hnum_4region.Fill(-1,tmp_event_weight );
              if tmp_jet_mass >=self.mj_signal_min and tmp_jet_mass <self.mj_signal_max : 
                 hnum_4region.Fill(0,tmp_event_weight);
              if tmp_jet_mass >=self.mj_sideband_hi_min and tmp_jet_mass <self.mj_sideband_hi_max: 
                 hnum_4region.Fill(1,tmp_event_weight);
              hnum_4region.Fill(2,tmp_event_weight);

             ## JES UP
             
             rrv_mass_lvj.setVal(mass_lvj_jes_up);
             rrv_mass_j.setVal(tmp_jet_mass_jes_up);

             if tmp_jet_mass_jes_up >= self.mj_sideband_lo_min and tmp_jet_mass_jes_up < self.mj_sideband_lo_max and isFullVBF_jes_up == 2:
                 rdataset_sb_lo_mlvj_jes_up.add( RooArgSet( rrv_mass_lvj ), tmp_event_weight );
                 rdataset4fit_sb_lo_mlvj_jes_up.add( RooArgSet( rrv_mass_lvj ), tmp_event_weight4fit );
                 data_category.setLabel("sideband");
                 combData_jes_up.add(RooArgSet(rrv_mass_lvj,data_category),tmp_event_weight);
                 combData4fit_jes_up.add(RooArgSet(rrv_mass_lvj,data_category),tmp_event_weight4fit);

             if tmp_jet_mass_jes_up >= self.mj_signal_min and tmp_jet_mass_jes_up < self.mj_signal_max and isFullVBF_jes_up == 2:
                 rdataset_signal_region_mlvj_jes_up.add( RooArgSet( rrv_mass_lvj ), tmp_event_weight );
                 rdataset4fit_signal_region_mlvj_jes_up.add( RooArgSet( rrv_mass_lvj ), tmp_event_weight4fit );
                 data_category.setLabel("signal_region");
                 combData_jes_up.add(RooArgSet(rrv_mass_lvj,data_category),tmp_event_weight);
                 combData4fit_jes_up.add(RooArgSet(rrv_mass_lvj,data_category),tmp_event_weight4fit);
                 hnum_2region_jes_up.Fill(1,tmp_event_weight);
                 if mass_lvj_jes_up >=self.mlvj_signal_min and mass_lvj_jes_up <self.mlvj_signal_max: 
                   hnum_2region_jes_up.Fill(0,tmp_event_weight);
                   
             if tmp_jet_mass_jes_up >= self.mj_sideband_hi_min and tmp_jet_mass_jes_up < self.mj_sideband_hi_max and isFullVBF_jes_up == 2:
                 rdataset_sb_hi_mlvj_jes_up.add( RooArgSet( rrv_mass_lvj ), tmp_event_weight );
                 rdataset4fit_sb_hi_mlvj_jes_up.add( RooArgSet( rrv_mass_lvj ), tmp_event_weight4fit );

             if tmp_jet_mass_jes_up >= self.mj_sideband_hi_min and tmp_jet_mass_jes_up < self.mj_sideband_hi_max and isFullVBF_jes_up ==1:
                 rdataset_sb_hi_mlvj_jes_up_relaxed.add( RooArgSet( rrv_mass_lvj ), tmp_event_weight );
                 rdataset4fit_sb_hi_mlvj_jes_up_relaxed.add( RooArgSet( rrv_mass_lvj ), tmp_event_weight4fit );

             if isFullVBF_jes_up == 2: 
              rdataset_mj_jes_up.add( RooArgSet( rrv_mass_j ), tmp_event_weight );
              rdataset4fit_mj_jes_up.add( RooArgSet( rrv_mass_j ), tmp_event_weight4fit );
              if tmp_jet_mass_jes_up >=self.mj_sideband_lo_min and tmp_jet_mass_jes_up <self.mj_sideband_lo_max: 
                 hnum_4region_jes_up.Fill(-1,tmp_event_weight );
              if tmp_jet_mass_jes_up >=self.mj_signal_min and tmp_jet_mass_jes_up <self.mj_signal_max : 
                 hnum_4region_jes_up.Fill(0,tmp_event_weight);
              if tmp_jet_mass_jes_up >=self.mj_sideband_hi_min and tmp_jet_mass_jes_up <self.mj_sideband_hi_max: 
                 hnum_4region_jes_up.Fill(1,tmp_event_weight);
              hnum_4region_jes_up.Fill(2,tmp_event_weight);


             ### jes dn
             rrv_mass_lvj.setVal(mass_lvj_jes_dn);
             rrv_mass_j.setVal(tmp_jet_mass_jes_dn);

             if tmp_jet_mass_jes_dn >= self.mj_sideband_lo_min and tmp_jet_mass_jes_dn < self.mj_sideband_lo_max and isFullVBF_jes_dn == 2:
                 rdataset_sb_lo_mlvj_jes_dn.add( RooArgSet( rrv_mass_lvj ), tmp_event_weight );
                 rdataset4fit_sb_lo_mlvj_jes_dn.add( RooArgSet( rrv_mass_lvj ), tmp_event_weight4fit );
                 data_category.setLabel("sideband");
                 combData_jes_dn.add(RooArgSet(rrv_mass_lvj,data_category),tmp_event_weight);
                 combData4fit_jes_dn.add(RooArgSet(rrv_mass_lvj,data_category),tmp_event_weight4fit);

             if tmp_jet_mass_jes_dn >= self.mj_signal_min and tmp_jet_mass_jes_dn < self.mj_signal_max and isFullVBF_jes_dn == 2:
                 rdataset_signal_region_mlvj_jes_dn.add( RooArgSet( rrv_mass_lvj ), tmp_event_weight );
                 rdataset4fit_signal_region_mlvj_jes_dn.add( RooArgSet( rrv_mass_lvj ), tmp_event_weight4fit );
                 data_category.setLabel("signal_region");
                 combData_jes_dn.add(RooArgSet(rrv_mass_lvj,data_category),tmp_event_weight);
                 combData4fit_jes_dn.add(RooArgSet(rrv_mass_lvj,data_category),tmp_event_weight4fit);
                 hnum_2region_jes_dn.Fill(1,tmp_event_weight);
                 if mass_lvj_jes_dn >=self.mlvj_signal_min and mass_lvj_jes_dn <self.mlvj_signal_max: 
                   hnum_2region_jes_dn.Fill(0,tmp_event_weight);
                   

             if tmp_jet_mass_jes_dn >= self.mj_sideband_hi_min and tmp_jet_mass_jes_dn < self.mj_sideband_hi_max and isFullVBF_jes_dn == 2:
                 rdataset_sb_hi_mlvj_jes_dn.add( RooArgSet( rrv_mass_lvj ), tmp_event_weight );
                 rdataset4fit_sb_hi_mlvj_jes_dn.add( RooArgSet( rrv_mass_lvj ), tmp_event_weight4fit );

             if isFullVBF_jes_dn == 2: 
              rdataset_mj_jes_dn.add( RooArgSet( rrv_mass_j ), tmp_event_weight );
              rdataset4fit_mj_jes_dn.add( RooArgSet( rrv_mass_j ), tmp_event_weight4fit );
              if tmp_jet_mass_jes_dn >=self.mj_sideband_lo_min and tmp_jet_mass_jes_dn <self.mj_sideband_lo_max: 
                 hnum_4region_jes_dn.Fill(-1,tmp_event_weight );
              if tmp_jet_mass_jes_dn >=self.mj_signal_min and tmp_jet_mass_jes_dn <self.mj_signal_max : 
                 hnum_4region_jes_dn.Fill(0,tmp_event_weight);
              if tmp_jet_mass_jes_dn >=self.mj_sideband_hi_min and tmp_jet_mass_jes_dn <self.mj_sideband_hi_max: 
                 hnum_4region_jes_dn.Fill(1,tmp_event_weight);
              hnum_4region_jes_dn.Fill(2,tmp_event_weight);


             ########################JER
             rrv_mass_lvj.setVal(mass_lvj_jer);
             rrv_mass_j.setVal(tmp_jet_mass_jer);

             if tmp_jet_mass_jer >= self.mj_sideband_lo_min and tmp_jet_mass_jer < self.mj_sideband_lo_max and isFullVBF_jer == 2:
                 rdataset_sb_lo_mlvj_jer.add( RooArgSet( rrv_mass_lvj ), tmp_event_weight );
                 rdataset4fit_sb_lo_mlvj_jer.add( RooArgSet( rrv_mass_lvj ), tmp_event_weight4fit );
                 data_category.setLabel("sideband");
                 combData_jer.add(RooArgSet(rrv_mass_lvj,data_category),tmp_event_weight);
                 combData4fit_jer.add(RooArgSet(rrv_mass_lvj,data_category),tmp_event_weight4fit);

             if tmp_jet_mass_jer >= self.mj_signal_min and tmp_jet_mass_jer < self.mj_signal_max and isFullVBF_jer == 2:
                 rdataset_signal_region_mlvj_jer.add( RooArgSet( rrv_mass_lvj ), tmp_event_weight );
                 rdataset4fit_signal_region_mlvj_jer.add( RooArgSet( rrv_mass_lvj ), tmp_event_weight4fit );
                 data_category.setLabel("signal_region");
                 combData_jer.add(RooArgSet(rrv_mass_lvj,data_category),tmp_event_weight);
                 combData4fit_jer.add(RooArgSet(rrv_mass_lvj,data_category),tmp_event_weight4fit);
                 hnum_2region_jer.Fill(1,tmp_event_weight);
                 if mass_lvj_jer >=self.mlvj_signal_min and mass_lvj_jer <self.mlvj_signal_max: 
                   hnum_2region_jer.Fill(0,tmp_event_weight);
                   
             if tmp_jet_mass_jer >= self.mj_sideband_hi_min and tmp_jet_mass_jer < self.mj_sideband_hi_max and isFullVBF_jer == 2:
                 rdataset_sb_hi_mlvj_jer.add( RooArgSet( rrv_mass_lvj ), tmp_event_weight );
                 rdataset4fit_sb_hi_mlvj_jer.add( RooArgSet( rrv_mass_lvj ), tmp_event_weight4fit );

             if isFullVBF_jer == 2: 
              rdataset_mj_jer.add( RooArgSet( rrv_mass_j ), tmp_event_weight );
              rdataset4fit_mj_jer.add( RooArgSet( rrv_mass_j ), tmp_event_weight4fit );
              if tmp_jet_mass_jer >=self.mj_sideband_lo_min and tmp_jet_mass_jer <self.mj_sideband_lo_max: 
                 hnum_4region_jer.Fill(-1,tmp_event_weight );
              if tmp_jet_mass_jer >=self.mj_signal_min and tmp_jet_mass_jer <self.mj_signal_max : 
                 hnum_4region_jer.Fill(0,tmp_event_weight);
              if tmp_jet_mass_jer >=self.mj_sideband_hi_min and tmp_jet_mass_jer <self.mj_sideband_hi_max: 
                 hnum_4region_jer.Fill(1,tmp_event_weight);
              hnum_4region_jer.Fill(2,tmp_event_weight);

             ########################JER_UP
             rrv_mass_lvj.setVal(mass_lvj_jer_up);
             rrv_mass_j.setVal(tmp_jet_mass_jer_up);

             if tmp_jet_mass_jer_up >= self.mj_sideband_lo_min and tmp_jet_mass_jer_up < self.mj_sideband_lo_max and isFullVBF_jer_up == 2:
                 rdataset_sb_lo_mlvj_jer_up.add( RooArgSet( rrv_mass_lvj ), tmp_event_weight );
                 rdataset4fit_sb_lo_mlvj_jer_up.add( RooArgSet( rrv_mass_lvj ), tmp_event_weight4fit );
                 data_category.setLabel("sideband");
                 combData_jer_up.add(RooArgSet(rrv_mass_lvj,data_category),tmp_event_weight);
                 combData4fit_jer_up.add(RooArgSet(rrv_mass_lvj,data_category),tmp_event_weight4fit);

             if tmp_jet_mass_jer_up >= self.mj_signal_min and tmp_jet_mass_jer_up < self.mj_signal_max and isFullVBF_jer_up == 2:
                 rdataset_signal_region_mlvj_jer_up.add( RooArgSet( rrv_mass_lvj ), tmp_event_weight );
                 rdataset4fit_signal_region_mlvj_jer_up.add( RooArgSet( rrv_mass_lvj ), tmp_event_weight4fit );
                 data_category.setLabel("signal_region");
                 combData_jer_up.add(RooArgSet(rrv_mass_lvj,data_category),tmp_event_weight);
                 combData4fit_jer_up.add(RooArgSet(rrv_mass_lvj,data_category),tmp_event_weight4fit);
                 hnum_2region_jer_up.Fill(1,tmp_event_weight);
                 if mass_lvj_jer_up >=self.mlvj_signal_min and mass_lvj_jer_up <self.mlvj_signal_max: 
                   hnum_2region_jer_up.Fill(0,tmp_event_weight);
                   
             if tmp_jet_mass_jer_up >= self.mj_sideband_hi_min and tmp_jet_mass_jer_up < self.mj_sideband_hi_max and isFullVBF_jer_up == 2:
                 rdataset_sb_hi_mlvj_jer_up.add( RooArgSet( rrv_mass_lvj ), tmp_event_weight );
                 rdataset4fit_sb_hi_mlvj_jer_up.add( RooArgSet( rrv_mass_lvj ), tmp_event_weight4fit );

             if isFullVBF_jer_up == 2: 
              rdataset_mj_jer_up.add( RooArgSet( rrv_mass_j ), tmp_event_weight );
              rdataset4fit_mj_jer_up.add( RooArgSet( rrv_mass_j ), tmp_event_weight4fit );
              if tmp_jet_mass_jer_up >=self.mj_sideband_lo_min and tmp_jet_mass_jer_up <self.mj_sideband_lo_max: 
                 hnum_4region_jer_up.Fill(-1,tmp_event_weight );
              if tmp_jet_mass_jer_up >=self.mj_signal_min and tmp_jet_mass_jer_up <self.mj_signal_max : 
                 hnum_4region_jer_up.Fill(0,tmp_event_weight);
              if tmp_jet_mass_jer_up >=self.mj_sideband_hi_min and tmp_jet_mass_jer_up <self.mj_sideband_hi_max: 
                 hnum_4region_jer_up.Fill(1,tmp_event_weight);
              hnum_4region_jer_up.Fill(2,tmp_event_weight);

             ########################JER_DN
             rrv_mass_lvj.setVal(mass_lvj_jer_dn);
             rrv_mass_j.setVal(tmp_jet_mass_jer_dn);

             if tmp_jet_mass_jer_dn >= self.mj_sideband_lo_min and tmp_jet_mass_jer_dn < self.mj_sideband_lo_max and isFullVBF_jer_dn == 2:
                 rdataset_sb_lo_mlvj_jer_dn.add( RooArgSet( rrv_mass_lvj ), tmp_event_weight );
                 rdataset4fit_sb_lo_mlvj_jer_dn.add( RooArgSet( rrv_mass_lvj ), tmp_event_weight4fit );
                 data_category.setLabel("sideband");
                 combData_jer_dn.add(RooArgSet(rrv_mass_lvj,data_category),tmp_event_weight);
                 combData4fit_jer_dn.add(RooArgSet(rrv_mass_lvj,data_category),tmp_event_weight4fit);

             if tmp_jet_mass_jer_dn >= self.mj_signal_min and tmp_jet_mass_jer_dn < self.mj_signal_max and isFullVBF_jer_dn == 2:
                 rdataset_signal_region_mlvj_jer_dn.add( RooArgSet( rrv_mass_lvj ), tmp_event_weight );
                 rdataset4fit_signal_region_mlvj_jer_dn.add( RooArgSet( rrv_mass_lvj ), tmp_event_weight4fit );
                 data_category.setLabel("signal_region");
                 combData_jer_dn.add(RooArgSet(rrv_mass_lvj,data_category),tmp_event_weight);
                 combData4fit_jer_dn.add(RooArgSet(rrv_mass_lvj,data_category),tmp_event_weight4fit);
                 hnum_2region_jer_dn.Fill(1,tmp_event_weight);
                 if mass_lvj_jer_dn >=self.mlvj_signal_min and mass_lvj_jer_dn <self.mlvj_signal_max: 
                   hnum_2region_jer_dn.Fill(0,tmp_event_weight);
                   
             if tmp_jet_mass_jer_dn >= self.mj_sideband_hi_min and tmp_jet_mass_jer_dn < self.mj_sideband_hi_max and isFullVBF_jer_dn == 2:
                 rdataset_sb_hi_mlvj_jer_dn.add( RooArgSet( rrv_mass_lvj ), tmp_event_weight );
                 rdataset4fit_sb_hi_mlvj_jer_dn.add( RooArgSet( rrv_mass_lvj ), tmp_event_weight4fit );

             if isFullVBF_jer_dn == 2: 
              rdataset_mj_jer_dn.add( RooArgSet( rrv_mass_j ), tmp_event_weight );
              rdataset4fit_mj_jer_dn.add( RooArgSet( rrv_mass_j ), tmp_event_weight4fit );
              if tmp_jet_mass_jer_dn >=self.mj_sideband_lo_min and tmp_jet_mass_jer_dn <self.mj_sideband_lo_max: 
                 hnum_4region_jer_dn.Fill(-1,tmp_event_weight );
              if tmp_jet_mass_jer_dn >=self.mj_signal_min and tmp_jet_mass_jer_dn <self.mj_signal_max : 
                 hnum_4region_jer_dn.Fill(0,tmp_event_weight);
              if tmp_jet_mass_jer_dn >=self.mj_sideband_hi_min and tmp_jet_mass_jer_dn <self.mj_sideband_hi_max: 
                 hnum_4region_jer_dn.Fill(1,tmp_event_weight);
              hnum_4region_jer_dn.Fill(2,tmp_event_weight);
                            
                                                              
        ## scale 4fit dataset in order to have the right luminosity normalization
        rrv_scale_to_lumi = RooRealVar("rrv_scale_to_lumi"+label+"_"+self.channel,"rrv_scale_to_lumi"+label+"_"+self.channel,rdataset_mj.sumEntries()/rdataset4fit_mj.sumEntries());
        rrv_scale_to_lumi.Print();
        rrv_scale_to_lumi_sb_lo = RooRealVar("rrv_scale_to_lumi"+label+"_"+self.channel+"_sb_lo_mlvj","rrv_scale_to_lumi"+label+"_"+self.channel+"_sb_lo_mlvj",0);
        if rdataset4fit_sb_lo_mlvj.sumEntries() != 0: 
         rrv_scale_to_lumi_sb_lo.setVal(rdataset_sb_lo_mlvj.sumEntries()/rdataset4fit_sb_lo_mlvj.sumEntries());
        rrv_scale_to_lumi_sb_lo.Print();
        rrv_scale_to_lumi_sb_hi = RooRealVar("rrv_scale_to_lumi"+label+"_"+self.channel+"_sb_hi_mlvj","rrv_scale_to_lumi"+label+"_"+self.channel+"_sb_hi_mlvj",rdataset_sb_hi_mlvj.sumEntries()/rdataset4fit_sb_hi_mlvj.sumEntries());
        rrv_scale_to_lumi_sb_hi.Print();
        rrv_scale_to_lumi_signal_region = RooRealVar("rrv_scale_to_lumi"+label+"_"+self.channel+"_signal_region_mlvj","rrv_scale_to_lumi"+label+"_"+self.channel+"_signal_region_mlvj",rdataset_signal_region_mlvj.sumEntries()/rdataset4fit_signal_region_mlvj.sumEntries());
        rrv_scale_to_lumi_signal_region.Print();
        getattr(self.workspace4fit_,"import")(rrv_scale_to_lumi);
        getattr(self.workspace4fit_,"import")(rrv_scale_to_lumi_sb_lo);
        getattr(self.workspace4fit_,"import")(rrv_scale_to_lumi_sb_hi);
        getattr(self.workspace4fit_,"import")(rrv_scale_to_lumi_signal_region);


        
        ## rescale factor for relaxed event in the sideband and signal region to match normalization after vbf cuts
        '''
        rrv_vbf_cut_sideband_lo = RooRealVar("rrv_vbf_cut_sb_lo"+label+"_"+self.channel,"rrv_vbf_cut_sb_lo"+label+"_"+self.channel,rdataset4fit_sb_lo_mlvj.sumEntries()/rdataset4fit_sb_lo_mlvj_relaxed.sumEntries());

        rrv_vbf_cut_sideband_hi = RooRealVar("rrv_vbf_cut_sb_hi"+label+"_"+self.channel,"rrv_vbf_cut_sb_hi"+label+"_"+self.channel,rdataset4fit_sb_hi_mlvj.sumEntries()/rdataset4fit_sb_hi_mlvj_relaxed.sumEntries());
            
        rrv_vbf_cut_signal_region = RooRealVar("rrv_vbf_cut_signal_region"+label+"_"+self.channel,"rrv_vbf_cut_signal_region"+label+"_"+self.channel,rdataset4fit_signal_region_mlvj.sumEntries()/rdataset4fit_signal_region_mlvj_relaxed.sumEntries());

        rrv_vbf_cut_total = RooRealVar("rrv_vbf_cut_total"+label+"_"+self.channel,"rrv_vbf_cut_total"+label+"_"+self.channel,rdataset4fit_mj.sumEntries()/rdataset4fit_mj_relaxed.sumEntries());

        getattr(self.workspace4fit_,"import")(rrv_vbf_cut_sideband_lo); rrv_vbf_cut_sideband_lo.Print();
        getattr(self.workspace4fit_,"import")(rrv_vbf_cut_sideband_hi);  rrv_vbf_cut_sideband_hi.Print();
        getattr(self.workspace4fit_,"import")(rrv_vbf_cut_signal_region); rrv_vbf_cut_signal_region.Print();
        getattr(self.workspace4fit_,"import")(rrv_vbf_cut_total); rrv_vbf_cut_total.Print();
        '''

        print "########### Nominal Value ###########";

        rrv_number_dataset_signal_region_mlvj = RooRealVar("rrv_number_dataset_signal_region"+label+"_"+self.channel+"_mlvj","rrv_number_dataset_signal_region"+label+"_"+self.channel+"_mlvj",hnum_2region.GetBinContent(1));       
        rrv_number_dataset_AllRange_mlvj = RooRealVar("rrv_number_dataset_AllRange"+label+"_"+self.channel+"_mlvj","rrv_number_dataset_AllRange"+label+"_"+self.channel+"_mlvj",hnum_2region.GetBinContent(2));
               
        getattr(self.workspace4fit_,"import")(rrv_number_dataset_signal_region_mlvj); rrv_number_dataset_signal_region_mlvj.Print();
        getattr(self.workspace4fit_,"import")(rrv_number_dataset_AllRange_mlvj); rrv_number_dataset_AllRange_mlvj.Print();
         
#        rrv_number_dataset_signal_region_mlvj_relaxed = RooRealVar("rrv_number_dataset_signal_region"+label+"_"+self.channel+"_mlvj_relaxed","rrv_number_dataset_signal_region"+label+"_"+self.channel+"_mlvj_relaxed",hnum_2region_relaxed.GetBinContent(1));       
#        rrv_number_dataset_AllRange_mlvj_relaxed = RooRealVar("rrv_number_dataset_AllRange"+label+"_"+self.channel+"_mlvj_relaxed","rrv_number_dataset_AllRange"+label+"_"+self.channel+"_mlvj_relaxed",hnum_2region_relaxed.GetBinContent(2));
               
#        getattr(self.workspace4fit_,"import")(rrv_number_dataset_signal_region_mlvj_relaxed); rrv_number_dataset_signal_region_mlvj_relaxed.Print();
#        getattr(self.workspace4fit_,"import")(rrv_number_dataset_AllRange_mlvj_relaxed); rrv_number_dataset_AllRange_mlvj_relaxed.Print();
        
        getattr(self.workspace4fit_,"import")(rdataset_sb_lo_mlvj); rdataset_sb_lo_mlvj.Print();
        getattr(self.workspace4fit_,"import")(rdataset_signal_region_mlvj); rdataset_signal_region_mlvj.Print();
        getattr(self.workspace4fit_,"import")(rdataset_sb_hi_mlvj); rdataset_sb_hi_mlvj.Print();
        getattr(self.workspace4fit_,"import")(rdataset4fit_sb_lo_mlvj); rdataset4fit_sb_lo_mlvj.Print();
        getattr(self.workspace4fit_,"import")(rdataset4fit_signal_region_mlvj); rdataset4fit_signal_region_mlvj.Print();
        getattr(self.workspace4fit_,"import")(rdataset4fit_sb_hi_mlvj); rdataset4fit_sb_hi_mlvj.Print();
        getattr(self.workspace4fit_,"import")(combData); combData.Print();
        getattr(self.workspace4fit_,"import")(combData4fit); combData4fit.Print();
        
#        getattr(self.workspace4fit_,"import")(rdataset_sb_lo_mlvj_relaxed); rdataset_sb_lo_mlvj_relaxed.Print();
#        getattr(self.workspace4fit_,"import")(rdataset_signal_region_mlvj_relaxed); rdataset_signal_region_mlvj_relaxed.Print();
#        getattr(self.workspace4fit_,"import")(rdataset_sb_hi_mlvj_relaxed); rdataset_sb_hi_mlvj_relaxed.Print();
#        getattr(self.workspace4fit_,"import")(rdataset4fit_sb_lo_mlvj_relaxed); rdataset4fit_sb_lo_mlvj_relaxed.Print();
#        getattr(self.workspace4fit_,"import")(rdataset4fit_signal_region_mlvj_relaxed); rdataset4fit_signal_region_mlvj_relaxed.Print();
#        getattr(self.workspace4fit_,"import")(rdataset4fit_sb_hi_mlvj_relaxed); rdataset4fit_sb_hi_mlvj_relaxed.Print();
#        getattr(self.workspace4fit_,"import")(combData_relaxed); combData_relaxed.Print();
#        getattr(self.workspace4fit_,"import")(combData4fit_relaxed); combData4fit_relaxed.Print();
 
        
        ###################jes_up
        print "########### jes up ###########";
        rrv_scale_to_lumi_jes_up = RooRealVar("rrv_scale_to_lumi"+label+"massvbf_jes_up_"+self.channel,"rrv_scale_to_lumi"+label+"massvbf_jes_up_"+self.channel,tmp_scale_to_lumi);
        rrv_scale_to_lumi_jes_up.Print();
        getattr(self.workspace4fit_,"import")(rrv_scale_to_lumi_jes_up);
        '''
        rrv_vbf_cut_sideband_lo_jes_up = RooRealVar("rrv_vbf_cut_sb_lo"+label+"massvbf_jes_up"+"_"+self.channel,"rrv_vbf_cut_sb_lo"+label+"massvbf_jes_up"+"_"+self.channel,rdataset4fit_sb_lo_mlvj_jes_up.sumEntries()/rdataset4fit_sb_lo_mlvj_jes_up_relaxed.sumEntries());
        rrv_vbf_cut_sideband_hi_jes_up = RooRealVar("rrv_vbf_cut_sb_hi"+label+"massvbf_jes_up"+"_"+self.channel,"rrv_vbf_cut_sb_hi"+label+"massvbf_jes_up"+"_"+self.channel,rdataset4fit_sb_hi_mlvj_jes_up.sumEntries()/rdataset4fit_sb_hi_mlvj_jes_up_relaxed.sumEntries());
        rrv_vbf_cut_signal_region_jes_up = RooRealVar("rrv_vbf_cut_signal_region"+label+"massvbf_jes_up"+"_"+self.channel,"rrv_vbf_cut_signal_region"+label+"massvbf_jes_up"+"_"+self.channel,rdataset4fit_signal_region_mlvj_jes_up.sumEntries()/rdataset4fit_signal_region_mlvj_jes_up_relaxed.sumEntries());
        rrv_vbf_cut_total_jes_up = RooRealVar("rrv_vbf_cut_total"+label+"massvbf_jes_up"+"_"+self.channel,"rrv_vbf_cut_total"+label+"massvbf_jes_up"+"_"+self.channel,rdataset4fit_mj_jes_up.sumEntries()/rdataset4fit_mj_jes_up_relaxed.sumEntries());

        getattr(self.workspace4fit_,"import")(rrv_vbf_cut_sideband_lo_jes_up); rrv_vbf_cut_sideband_lo_jes_up.Print();
        getattr(self.workspace4fit_,"import")(rrv_vbf_cut_sideband_hi_jes_up);  rrv_vbf_cut_sideband_hi_jes_up.Print();
        getattr(self.workspace4fit_,"import")(rrv_vbf_cut_signal_region_jes_up); rrv_vbf_cut_signal_region_jes_up.Print();
        getattr(self.workspace4fit_,"import")(rrv_vbf_cut_total_jes_up); rrv_vbf_cut_total_jes_up.Print();
        '''

        rrv_number_dataset_signal_region_mlvj_jes_up = RooRealVar("rrv_number_dataset_signal_region"+label+"massvbf_jes_up"+"_"+self.channel+"_mlvj","rrv_number_dataset_signal_region"+label+"massvbf_jes_up"+"_"+self.channel+"_mlvj",hnum_2region_jes_up.GetBinContent(1));       
        rrv_number_dataset_AllRange_mlvj_jes_up = RooRealVar("rrv_number_dataset_AllRange"+label+"massvbf_jes_up"+"_"+self.channel+"_mlvj","rrv_number_dataset_AllRange"+label+"massvbf_jes_up"+"_"+self.channel+"_mlvj",hnum_2region_jes_up.GetBinContent(2));
               
        getattr(self.workspace4fit_,"import")(rrv_number_dataset_signal_region_mlvj_jes_up); rrv_number_dataset_signal_region_mlvj_jes_up.Print();
        getattr(self.workspace4fit_,"import")(rrv_number_dataset_AllRange_mlvj_jes_up); rrv_number_dataset_AllRange_mlvj_jes_up.Print();
        
#        rrv_number_dataset_signal_region_mlvj_jes_up_relaxed = RooRealVar("rrv_number_dataset_signal_region"+label+"massvbf_jes_up"+"_"+self.channel+"_mlvj_relaxed","rrv_number_dataset_signal_region"+label+"massvbf_jes_up"+"_"+self.channel+"_mlvj_relaxed",hnum_2region_jes_up_relaxed.GetBinContent(1));       
#        rrv_number_dataset_AllRange_mlvj_jes_up_relaxed = RooRealVar("rrv_number_dataset_AllRange"+label+"massvbf_jes_up"+"_"+self.channel+"_mlvj_relaxed","rrv_number_dataset_AllRange"+label+"massvbf_jes_up"+"_"+self.channel+"_mlvj_relaxed",hnum_2region_jes_up_relaxed.GetBinContent(2));
               
#        getattr(self.workspace4fit_,"import")(rrv_number_dataset_signal_region_mlvj_jes_up_relaxed); rrv_number_dataset_signal_region_mlvj_jes_up_relaxed.Print();
#        getattr(self.workspace4fit_,"import")(rrv_number_dataset_AllRange_mlvj_jes_up_relaxed); rrv_number_dataset_AllRange_mlvj_jes_up_relaxed.Print();
               
        getattr(self.workspace4fit_,"import")(rdataset_sb_lo_mlvj_jes_up); rdataset_sb_lo_mlvj_jes_up.Print();
        getattr(self.workspace4fit_,"import")(rdataset_signal_region_mlvj_jes_up); rdataset_signal_region_mlvj_jes_up.Print();
        getattr(self.workspace4fit_,"import")(rdataset_sb_hi_mlvj_jes_up); rdataset_sb_hi_mlvj_jes_up.Print();
        getattr(self.workspace4fit_,"import")(rdataset4fit_sb_lo_mlvj_jes_up); rdataset4fit_sb_lo_mlvj_jes_up.Print();
        getattr(self.workspace4fit_,"import")(rdataset4fit_signal_region_mlvj_jes_up); rdataset4fit_signal_region_mlvj_jes_up.Print();
        getattr(self.workspace4fit_,"import")(rdataset4fit_sb_hi_mlvj_jes_up); rdataset4fit_sb_hi_mlvj_jes_up.Print();
        getattr(self.workspace4fit_,"import")(combData_jes_up); combData_jes_up.Print();
        getattr(self.workspace4fit_,"import")(combData4fit_jes_up); combData4fit_jes_up.Print();
#        getattr(self.workspace4fit_,"import")(rdataset_sb_lo_mlvj_jes_up_relaxed); rdataset_sb_lo_mlvj_jes_up_relaxed.Print();
#        getattr(self.workspace4fit_,"import")(rdataset_signal_region_mlvj_jes_up_relaxed); rdataset_signal_region_mlvj_jes_up_relaxed.Print();
#        getattr(self.workspace4fit_,"import")(rdataset_sb_hi_mlvj_jes_up_relaxed); rdataset_sb_hi_mlvj_jes_up_relaxed.Print();
#        getattr(self.workspace4fit_,"import")(rdataset4fit_sb_lo_mlvj_jes_up_relaxed); rdataset4fit_sb_lo_mlvj_jes_up_relaxed.Print(); 
#        getattr(self.workspace4fit_,"import")(rdataset4fit_signal_region_mlvj_jes_up_relaxed); rdataset4fit_signal_region_mlvj_jes_up_relaxed.Print();
#        getattr(self.workspace4fit_,"import")(rdataset4fit_sb_hi_mlvj_jes_up_relaxed); rdataset4fit_sb_hi_mlvj_jes_up_relaxed.Print();
#        getattr(self.workspace4fit_,"import")(combData_jes_up_relaxed); combData_jes_up_relaxed.Print();
#        getattr(self.workspace4fit_,"import")(combData4fit_jes_up_relaxed); combData4fit_jes_up_relaxed.Print();

        ####################jes_dn
        print "########### jes dn ###########";
        rrv_scale_to_lumi_jes_dn = RooRealVar("rrv_scale_to_lumi"+label+"massvbf_jes_dn_"+self.channel,"rrv_scale_to_lumi"+label+"massvbf_jes_dn_"+self.channel,tmp_scale_to_lumi);
        rrv_scale_to_lumi_jes_dn.Print();
        getattr(self.workspace4fit_,"import")(rrv_scale_to_lumi_jes_dn);

        '''
        rrv_vbf_cut_sideband_lo_jes_dn = RooRealVar("rrv_vbf_cut_sb_lo"+label+"massvbf_jes_dn"+"_"+self.channel,"rrv_vbf_cut_sb_lo"+label+"massvbf_jes_dn"+"_"+self.channel,rdataset4fit_sb_lo_mlvj_jes_dn.sumEntries()/rdataset4fit_sb_lo_mlvj_jes_dn_relaxed.sumEntries());
        rrv_vbf_cut_sideband_hi_jes_dn = RooRealVar("rrv_vbf_cut_sb_hi"+label+"massvbf_jes_dn"+"_"+self.channel,"rrv_vbf_cut_sb_hi"+label+"massvbf_jes_dn"+"_"+self.channel,rdataset4fit_sb_hi_mlvj_jes_dn.sumEntries()/rdataset4fit_sb_hi_mlvj_jes_dn_relaxed.sumEntries());
        rrv_vbf_cut_signal_region_jes_dn = RooRealVar("rrv_vbf_cut_signal_region"+label+"massvbf_jes_dn"+"_"+self.channel,"rrv_vbf_cut_signal_region"+label+"massvbf_jes_dn"+"_"+self.channel,rdataset4fit_signal_region_mlvj_jes_dn.sumEntries()/rdataset4fit_signal_region_mlvj_jes_dn_relaxed.sumEntries());
        rrv_vbf_cut_total_jes_dn = RooRealVar("rrv_vbf_cut_total"+label+"massvbf_jes_dn"+"_"+self.channel,"rrv_vbf_cut_total"+label+"massvbf_jes_dn"+"_"+self.channel,rdataset4fit_mj_jes_dn.sumEntries()/rdataset4fit_mj_jes_dn_relaxed.sumEntries());

        getattr(self.workspace4fit_,"import")(rrv_vbf_cut_sideband_lo_jes_dn); rrv_vbf_cut_sideband_lo_jes_dn.Print();
        getattr(self.workspace4fit_,"import")(rrv_vbf_cut_sideband_hi_jes_dn);  rrv_vbf_cut_sideband_hi_jes_dn.Print();
        getattr(self.workspace4fit_,"import")(rrv_vbf_cut_signal_region_jes_dn); rrv_vbf_cut_signal_region_jes_dn.Print();
        getattr(self.workspace4fit_,"import")(rrv_vbf_cut_total_jes_dn); rrv_vbf_cut_total_jes_dn.Print();
        '''

        rrv_number_dataset_signal_region_mlvj_jes_dn = RooRealVar("rrv_number_dataset_signal_region"+label+"massvbf_jes_dn"+"_"+self.channel+"_mlvj","rrv_number_dataset_signal_region"+label+"massvbf_jes_dn"+"_"+self.channel+"_mlvj",hnum_2region_jes_dn.GetBinContent(1));       
        rrv_number_dataset_AllRange_mlvj_jes_dn = RooRealVar("rrv_number_dataset_AllRange"+label+"massvbf_jes_dn"+"_"+self.channel+"_mlvj","rrv_number_dataset_AllRange"+label+"massvbf_jes_dn"+"_"+self.channel+"_mlvj",hnum_2region_jes_dn.GetBinContent(2));
               
        getattr(self.workspace4fit_,"import")(rrv_number_dataset_signal_region_mlvj_jes_dn); rrv_number_dataset_signal_region_mlvj_jes_dn.Print();
        getattr(self.workspace4fit_,"import")(rrv_number_dataset_AllRange_mlvj_jes_dn); rrv_number_dataset_AllRange_mlvj_jes_dn.Print();
        
#        rrv_number_dataset_signal_region_mlvj_jes_dn_relaxed = RooRealVar("rrv_number_dataset_signal_region"+label+"massvbf_jes_dn"+"_"+self.channel+"_mlvj_relaxed","rrv_number_dataset_signal_region"+label+"massvbf_jes_dn"+"_"+self.channel+"_mlvj_relaxed",hnum_2region_jes_dn_relaxed.GetBinContent(1));       
#        rrv_number_dataset_AllRange_mlvj_jes_dn_relaxed = RooRealVar("rrv_number_dataset_AllRange"+label+"massvbf_jes_dn"+"_"+self.channel+"_mlvj_relaxed","rrv_number_dataset_AllRange"+label+"massvbf_jes_dn"+"_"+self.channel+"_mlvj_relaxed",hnum_2region_jes_dn_relaxed.GetBinContent(2));
               
#        getattr(self.workspace4fit_,"import")(rrv_number_dataset_signal_region_mlvj_jes_dn_relaxed); rrv_number_dataset_signal_region_mlvj_jes_dn_relaxed.Print();
#        getattr(self.workspace4fit_,"import")(rrv_number_dataset_AllRange_mlvj_jes_dn_relaxed); rrv_number_dataset_AllRange_mlvj_jes_dn_relaxed.Print();
               
        getattr(self.workspace4fit_,"import")(rdataset_sb_lo_mlvj_jes_dn); rdataset_sb_lo_mlvj_jes_dn.Print();
        getattr(self.workspace4fit_,"import")(rdataset_signal_region_mlvj_jes_dn); rdataset_signal_region_mlvj_jes_dn.Print();
        getattr(self.workspace4fit_,"import")(rdataset_sb_hi_mlvj_jes_dn); rdataset_sb_hi_mlvj_jes_dn.Print();
        getattr(self.workspace4fit_,"import")(rdataset4fit_sb_lo_mlvj_jes_dn); rdataset4fit_sb_lo_mlvj_jes_dn.Print();
        getattr(self.workspace4fit_,"import")(rdataset4fit_signal_region_mlvj_jes_dn); rdataset4fit_signal_region_mlvj_jes_dn.Print();
        getattr(self.workspace4fit_,"import")(rdataset4fit_sb_hi_mlvj_jes_dn); rdataset4fit_sb_hi_mlvj_jes_dn.Print();
        getattr(self.workspace4fit_,"import")(combData_jes_dn); combData_jes_dn.Print();
        getattr(self.workspace4fit_,"import")(combData4fit_jes_dn); combData4fit_jes_dn.Print();
#        getattr(self.workspace4fit_,"import")(rdataset_sb_lo_mlvj_jes_dn_relaxed); rdataset_sb_lo_mlvj_jes_dn_relaxed.Print();
#        getattr(self.workspace4fit_,"import")(rdataset_signal_region_mlvj_jes_dn_relaxed); rdataset_signal_region_mlvj_jes_dn_relaxed.Print();
#        getattr(self.workspace4fit_,"import")(rdataset_sb_hi_mlvj_jes_dn_relaxed); rdataset_sb_hi_mlvj_jes_dn_relaxed.Print();
#        getattr(self.workspace4fit_,"import")(rdataset4fit_sb_lo_mlvj_jes_dn_relaxed); rdataset4fit_sb_lo_mlvj_jes_dn_relaxed.Print();
#        getattr(self.workspace4fit_,"import")(rdataset4fit_signal_region_mlvj_jes_dn_relaxed); rdataset4fit_signal_region_mlvj_jes_dn_relaxed.Print();
#        getattr(self.workspace4fit_,"import")(rdataset4fit_sb_hi_mlvj_jes_dn_relaxed); rdataset4fit_sb_hi_mlvj_jes_dn_relaxed.Print();
#        getattr(self.workspace4fit_,"import")(combData_jes_dn_relaxed); combData_jes_dn_relaxed.Print();
#        getattr(self.workspace4fit_,"import")(combData4fit_jes_dn_relaxed); combData4fit_jes_dn_relaxed.Print();


        ####################jer
        print "########### jer ###########";
        rrv_scale_to_lumi_jer = RooRealVar("rrv_scale_to_lumi"+label+"massvbf_jer_"+self.channel,"rrv_scale_to_lumi"+label+"massvbf_jer_"+self.channel,tmp_scale_to_lumi);
        rrv_scale_to_lumi_jer.Print();
        getattr(self.workspace4fit_,"import")(rrv_scale_to_lumi_jer);

        '''
        rrv_vbf_cut_sideband_lo_jer = RooRealVar("rrv_vbf_cut_sb_lo"+label+"massvbf_jer"+"_"+self.channel,"rrv_vbf_cut_sb_lo"+label+"massvbf_jer"+"_"+self.channel,rdataset4fit_sb_lo_mlvj_jer.sumEntries()/rdataset4fit_sb_lo_mlvj_jer_relaxed.sumEntries());
        rrv_vbf_cut_sideband_hi_jer = RooRealVar("rrv_vbf_cut_sb_hi"+label+"massvbf_jer"+"_"+self.channel,"rrv_vbf_cut_sb_hi"+label+"massvbf_jer"+"_"+self.channel,rdataset4fit_sb_hi_mlvj_jer.sumEntries()/rdataset4fit_sb_hi_mlvj_jer_relaxed.sumEntries());
        rrv_vbf_cut_signal_region_jer = RooRealVar("rrv_vbf_cut_signal_region"+label+"massvbf_jer"+"_"+self.channel,"rrv_vbf_cut_signal_region"+label+"massvbf_jer"+"_"+self.channel,rdataset4fit_signal_region_mlvj_jer.sumEntries()/rdataset4fit_signal_region_mlvj_jer_relaxed.sumEntries());
        rrv_vbf_cut_total_jer = RooRealVar("rrv_vbf_cut_total"+label+"massvbf_jer"+"_"+self.channel,"rrv_vbf_cut_total"+label+"massvbf_jer"+"_"+self.channel,rdataset4fit_mj_jer.sumEntries()/rdataset4fit_mj_jer_relaxed.sumEntries());

        getattr(self.workspace4fit_,"import")(rrv_vbf_cut_sideband_lo_jer); rrv_vbf_cut_sideband_lo_jer.Print();
        getattr(self.workspace4fit_,"import")(rrv_vbf_cut_sideband_hi_jer);  rrv_vbf_cut_sideband_hi_jer.Print();
        getattr(self.workspace4fit_,"import")(rrv_vbf_cut_signal_region_jer); rrv_vbf_cut_signal_region_jer.Print();
        getattr(self.workspace4fit_,"import")(rrv_vbf_cut_total_jer); rrv_vbf_cut_total_jer.Print();
        '''

        rrv_number_dataset_signal_region_mlvj_jer = RooRealVar("rrv_number_dataset_signal_region"+label+"massvbf_jer"+"_"+self.channel+"_mlvj","rrv_number_dataset_signal_region"+label+"massvbf_jer"+"_"+self.channel+"_mlvj",hnum_2region_jer.GetBinContent(1));       
        rrv_number_dataset_AllRange_mlvj_jer = RooRealVar("rrv_number_dataset_AllRange"+label+"massvbf_jer"+"_"+self.channel+"_mlvj","rrv_number_dataset_AllRange"+label+"massvbf_jer"+"_"+self.channel+"_mlvj",hnum_2region_jer.GetBinContent(2));
               
        getattr(self.workspace4fit_,"import")(rrv_number_dataset_signal_region_mlvj_jer); rrv_number_dataset_signal_region_mlvj_jer.Print();
        getattr(self.workspace4fit_,"import")(rrv_number_dataset_AllRange_mlvj_jer); rrv_number_dataset_AllRange_mlvj_jer.Print();
        
#        rrv_number_dataset_signal_region_mlvj_jer_relaxed = RooRealVar("rrv_number_dataset_signal_region"+label+"massvbf_jer"+"_"+self.channel+"_mlvj_relaxed","rrv_number_dataset_signal_region"+label+"massvbf_jer"+"_"+self.channel+"_mlvj_relaxed",hnum_2region_jer_relaxed.GetBinContent(1));       
#        rrv_number_dataset_AllRange_mlvj_jer_relaxed = RooRealVar("rrv_number_dataset_AllRange"+label+"jetres"+"_"+self.channel+"_mlvj_relaxed","rrv_number_dataset_AllRange"+label+"jetres"+"_"+self.channel+"_mlvj_relaxed",hnum_2region_jer_relaxed.GetBinContent(2));
               
#        getattr(self.workspace4fit_,"import")(rrv_number_dataset_signal_region_mlvj_jer_relaxed); rrv_number_dataset_signal_region_mlvj_jer_relaxed.Print();
#        getattr(self.workspace4fit_,"import")(rrv_number_dataset_AllRange_mlvj_jer_relaxed); rrv_number_dataset_AllRange_mlvj_jer_relaxed.Print();
               
        getattr(self.workspace4fit_,"import")(rdataset_sb_lo_mlvj_jer); rdataset_sb_lo_mlvj_jer.Print();
        getattr(self.workspace4fit_,"import")(rdataset_signal_region_mlvj_jer); rdataset_signal_region_mlvj_jer.Print();
        getattr(self.workspace4fit_,"import")(rdataset_sb_hi_mlvj_jer); rdataset_sb_hi_mlvj_jer.Print();
        getattr(self.workspace4fit_,"import")(rdataset4fit_sb_lo_mlvj_jer); rdataset4fit_sb_lo_mlvj_jer.Print();
        getattr(self.workspace4fit_,"import")(rdataset4fit_signal_region_mlvj_jer); rdataset4fit_signal_region_mlvj_jer.Print();
        getattr(self.workspace4fit_,"import")(rdataset4fit_sb_hi_mlvj_jer); rdataset4fit_sb_hi_mlvj_jer.Print();
        getattr(self.workspace4fit_,"import")(combData_jer); combData_jer.Print();
        getattr(self.workspace4fit_,"import")(combData4fit_jer); combData4fit_jer.Print();
#        getattr(self.workspace4fit_,"import")(rdataset_sb_lo_mlvj_jer_relaxed); rdataset_sb_lo_mlvj_jer_relaxed.Print();
#        getattr(self.workspace4fit_,"import")(rdataset_signal_region_mlvj_jer_relaxed); rdataset_signal_region_mlvj_jer_relaxed.Print();
#        getattr(self.workspace4fit_,"import")(rdataset_sb_hi_mlvj_jer_relaxed); rdataset_sb_hi_mlvj_jer_relaxed.Print();
#        getattr(self.workspace4fit_,"import")(rdataset4fit_sb_lo_mlvj_jer_relaxed); rdataset4fit_sb_lo_mlvj_jer_relaxed.Print();
#        getattr(self.workspace4fit_,"import")(rdataset4fit_signal_region_mlvj_jer_relaxed); rdataset4fit_signal_region_mlvj_jer_relaxed.Print();
#        getattr(self.workspace4fit_,"import")(rdataset4fit_sb_hi_mlvj_jer_relaxed); rdataset4fit_sb_hi_mlvj_jer_relaxed.Print();
#        getattr(self.workspace4fit_,"import")(combData_jer_relaxed); combData_jer_relaxed.Print();
#        getattr(self.workspace4fit_,"import")(combData4fit_jer_relaxed); combData4fit_jer_relaxed.Print();


        ####################jer_up
        print "########### jer up ###########";
        rrv_scale_to_lumi_jer_up = RooRealVar("rrv_scale_to_lumi"+label+"massvbf_jer_up_"+self.channel,"rrv_scale_to_lumi"+label+"massvbf_jer_up_"+self.channel,tmp_scale_to_lumi);
        rrv_scale_to_lumi_jer_up.Print();
        getattr(self.workspace4fit_,"import")(rrv_scale_to_lumi_jer_up);

        rrv_scale_to_lumi_jer_up = RooRealVar("rrv_scale_to_lumi"+label+"massvbf_jer_up_"+self.channel,"rrv_scale_to_lumi"+label+"massvbf_jer_up_"+self.channel,tmp_scale_to_lumi);
        rrv_scale_to_lumi_jer_up.Print();
        getattr(self.workspace4fit_,"import")(rrv_scale_to_lumi_jer_up);

        '''
        rrv_vbf_cut_sideband_lo_jer_up = RooRealVar("rrv_vbf_cut_sb_lo"+label+"massvbf_jer_up"+"_"+self.channel,"rrv_vbf_cut_sb_lo"+label+"massvbf_jer_up"+"_"+self.channel,rdataset4fit_sb_lo_mlvj_jer_up.sumEntries()/rdataset4fit_sb_lo_mlvj_jer_up_relaxed.sumEntries());
        rrv_vbf_cut_sideband_hi_jer_up = RooRealVar("rrv_vbf_cut_sb_hi"+label+"massvbf_jer_up"+"_"+self.channel,"rrv_vbf_cut_sb_hi"+label+"massvbf_jer_up"+"_"+self.channel,rdataset4fit_sb_hi_mlvj_jer_up.sumEntries()/rdataset4fit_sb_hi_mlvj_jer_up_relaxed.sumEntries());
        rrv_vbf_cut_signal_region_jer_up = RooRealVar("rrv_vbf_cut_signal_region"+label+"massvbf_jer_up"+"_"+self.channel,"rrv_vbf_cut_signal_region"+label+"massvbf_jer_up"+"_"+self.channel,rdataset4fit_signal_region_mlvj_jer_up.sumEntries()/rdataset4fit_signal_region_mlvj_jer_up_relaxed.sumEntries());
        rrv_vbf_cut_total_jer_up = RooRealVar("rrv_vbf_cut_total"+label+"massvbf_jer_up"+"_"+self.channel,"rrv_vbf_cut_total"+label+"massvbf_jer_up"+"_"+self.channel,rdataset4fit_mj_jer_up.sumEntries()/rdataset4fit_mj_jer_up_relaxed.sumEntries());

        getattr(self.workspace4fit_,"import")(rrv_vbf_cut_sideband_lo_jer_up); rrv_vbf_cut_sideband_lo_jer_up.Print();
        getattr(self.workspace4fit_,"import")(rrv_vbf_cut_sideband_hi_jer_up);  rrv_vbf_cut_sideband_hi_jer_up.Print();
        getattr(self.workspace4fit_,"import")(rrv_vbf_cut_signal_region_jer_up); rrv_vbf_cut_signal_region_jer_up.Print();
        getattr(self.workspace4fit_,"import")(rrv_vbf_cut_total_jer_up); rrv_vbf_cut_total_jer_up.Print();
        '''

        rrv_number_dataset_signal_region_mlvj_jer_up = RooRealVar("rrv_number_dataset_signal_region"+label+"massvbf_jer_up"+"_"+self.channel+"_mlvj","rrv_number_dataset_signal_region"+label+"massvbf_jer_up"+"_"+self.channel+"_mlvj",hnum_2region_jer_up.GetBinContent(1));       
        rrv_number_dataset_AllRange_mlvj_jer_up = RooRealVar("rrv_number_dataset_AllRange"+label+"massvbf_jer_up"+"_"+self.channel+"_mlvj","rrv_number_dataset_AllRange"+label+"massvbf_jer_up"+"_"+self.channel+"_mlvj",hnum_2region_jer_up.GetBinContent(2));
               
        getattr(self.workspace4fit_,"import")(rrv_number_dataset_signal_region_mlvj_jer_up); rrv_number_dataset_signal_region_mlvj_jer_up.Print();
        getattr(self.workspace4fit_,"import")(rrv_number_dataset_AllRange_mlvj_jer_up); rrv_number_dataset_AllRange_mlvj_jer_up.Print();
        
#        rrv_number_dataset_signal_region_mlvj_jer_up_relaxed = RooRealVar("rrv_number_dataset_signal_region"+label+"massvbf_jer_up"+"_"+self.channel+"_mlvj_relaxed","rrv_number_dataset_signal_region"+label+"massvbf_jer_up"+"_"+self.channel+"_mlvj_relaxed",hnum_2region_jer_up_relaxed.GetBinContent(1));       
#        rrv_number_dataset_AllRange_mlvj_jer_up_relaxed = RooRealVar("rrv_number_dataset_AllRange"+label+"massvbf_jer_up"+"_"+self.channel+"_mlvj_relaxed","rrv_number_dataset_AllRange"+label+"massvbf_jer_up"+"_"+self.channel+"_mlvj_relaxed",hnum_2region_jer_up_relaxed.GetBinContent(2));
               
#        getattr(self.workspace4fit_,"import")(rrv_number_dataset_signal_region_mlvj_jer_up_relaxed); rrv_number_dataset_signal_region_mlvj_jer_up_relaxed.Print();
#        getattr(self.workspace4fit_,"import")(rrv_number_dataset_AllRange_mlvj_jer_up_relaxed); rrv_number_dataset_AllRange_mlvj_jer_up_relaxed.Print();
               
        getattr(self.workspace4fit_,"import")(rdataset_sb_lo_mlvj_jer_up); rdataset_sb_lo_mlvj_jer_up.Print();
        getattr(self.workspace4fit_,"import")(rdataset_signal_region_mlvj_jer_up); rdataset_signal_region_mlvj_jer_up.Print();
        getattr(self.workspace4fit_,"import")(rdataset_sb_hi_mlvj_jer_up); rdataset_sb_hi_mlvj_jer_up.Print();
        getattr(self.workspace4fit_,"import")(rdataset4fit_sb_lo_mlvj_jer_up); rdataset4fit_sb_lo_mlvj_jer_up.Print();
        getattr(self.workspace4fit_,"import")(rdataset4fit_signal_region_mlvj_jer_up); rdataset4fit_signal_region_mlvj_jer_up.Print();
        getattr(self.workspace4fit_,"import")(rdataset4fit_sb_hi_mlvj_jer_up); rdataset4fit_sb_hi_mlvj_jer_up.Print();
        getattr(self.workspace4fit_,"import")(combData_jer_up); combData_jer_up.Print();
        getattr(self.workspace4fit_,"import")(combData4fit_jer_up); combData4fit_jer_up.Print();
#        getattr(self.workspace4fit_,"import")(rdataset_sb_lo_mlvj_jer_up_relaxed); rdataset_sb_lo_mlvj_jer_up_relaxed.Print();
#        getattr(self.workspace4fit_,"import")(rdataset_signal_region_mlvj_jer_up_relaxed); rdataset_signal_region_mlvj_jer_up_relaxed.Print();
#        getattr(self.workspace4fit_,"import")(rdataset_sb_hi_mlvj_jer_up_relaxed); rdataset_sb_hi_mlvj_jer_up_relaxed.Print();
#        getattr(self.workspace4fit_,"import")(rdataset4fit_sb_lo_mlvj_jer_up_relaxed); rdataset4fit_sb_lo_mlvj_jer_up_relaxed.Print();
#        getattr(self.workspace4fit_,"import")(rdataset4fit_signal_region_mlvj_jer_up_relaxed); rdataset4fit_signal_region_mlvj_jer_up_relaxed.Print();
#        getattr(self.workspace4fit_,"import")(rdataset4fit_sb_hi_mlvj_jer_up_relaxed); rdataset4fit_sb_hi_mlvj_jer_up_relaxed.Print();
#        getattr(self.workspace4fit_,"import")(combData_jer_up_relaxed); combData_jer_up_relaxed.Print();
#        getattr(self.workspace4fit_,"import")(combData4fit_jer_up_relaxed); combData4fit_jer_up_relaxed.Print();

        ####################jer_dn
        print "########### jer dn ###########";
        rrv_scale_to_lumi_jer_dn = RooRealVar("rrv_scale_to_lumi"+label+"massvbf_jer_dn_"+self.channel,"rrv_scale_to_lumi"+label+"massvbf_jer_dn_"+self.channel,tmp_scale_to_lumi);
        rrv_scale_to_lumi_jer_dn.Print();
        getattr(self.workspace4fit_,"import")(rrv_scale_to_lumi_jer_dn);

        '''
        rrv_vbf_cut_sideband_lo_jer_dn = RooRealVar("rrv_vbf_cut_sb_lo"+label+"massvbf_jer_dn"+"_"+self.channel,"rrv_vbf_cut_sb_lo"+label+"massvbf_jer_dn"+"_"+self.channel,rdataset4fit_sb_lo_mlvj_jer_dn.sumEntries()/rdataset4fit_sb_lo_mlvj_jer_dn_relaxed.sumEntries());
        rrv_vbf_cut_sideband_hi_jer_dn = RooRealVar("rrv_vbf_cut_sb_hi"+label+"massvbf_jer_dn"+"_"+self.channel,"rrv_vbf_cut_sb_hi"+label+"massvbf_jer_dn"+"_"+self.channel,rdataset4fit_sb_hi_mlvj_jer_dn.sumEntries()/rdataset4fit_sb_hi_mlvj_jer_dn_relaxed.sumEntries());
        rrv_vbf_cut_signal_region_jer_dn = RooRealVar("rrv_vbf_cut_signal_region"+label+"massvbf_jer_dn"+"_"+self.channel,"rrv_vbf_cut_signal_region"+label+"massvbf_jer_dn"+"_"+self.channel,rdataset4fit_signal_region_mlvj_jer_dn.sumEntries()/rdataset4fit_signal_region_mlvj_jer_dn_relaxed.sumEntries());
        rrv_vbf_cut_total_jer_dn = RooRealVar("rrv_vbf_cut_total"+label+"massvbf_jer_dn"+"_"+self.channel,"rrv_vbf_cut_total"+label+"massvbf_jer_dn"+"_"+self.channel,rdataset4fit_mj_jer_dn.sumEntries()/rdataset4fit_mj_jer_dn_relaxed.sumEntries());

        getattr(self.workspace4fit_,"import")(rrv_vbf_cut_sideband_lo_jer_dn); rrv_vbf_cut_sideband_lo_jer_dn.Print();
        getattr(self.workspace4fit_,"import")(rrv_vbf_cut_sideband_hi_jer_dn);  rrv_vbf_cut_sideband_hi_jer_dn.Print();
        getattr(self.workspace4fit_,"import")(rrv_vbf_cut_signal_region_jer_dn); rrv_vbf_cut_signal_region_jer_dn.Print();
        getattr(self.workspace4fit_,"import")(rrv_vbf_cut_total_jer_dn); rrv_vbf_cut_total_jer_dn.Print();
        '''

        rrv_number_dataset_signal_region_mlvj_jer_dn = RooRealVar("rrv_number_dataset_signal_region"+label+"massvbf_jer_dn"+"_"+self.channel+"_mlvj","rrv_number_dataset_signal_region"+label+"massvbf_jer_dn"+"_"+self.channel+"_mlvj",hnum_2region_jer_dn.GetBinContent(1));       
        rrv_number_dataset_AllRange_mlvj_jer_dn = RooRealVar("rrv_number_dataset_AllRange"+label+"massvbf_jer_dn"+"_"+self.channel+"_mlvj","rrv_number_dataset_AllRange"+label+"massvbf_jer_dn"+"_"+self.channel+"_mlvj",hnum_2region_jer_dn.GetBinContent(2));
               
        getattr(self.workspace4fit_,"import")(rrv_number_dataset_signal_region_mlvj_jer_dn); rrv_number_dataset_signal_region_mlvj_jer_dn.Print();
        getattr(self.workspace4fit_,"import")(rrv_number_dataset_AllRange_mlvj_jer_dn); rrv_number_dataset_AllRange_mlvj_jer_dn.Print();
        
#        rrv_number_dataset_signal_region_mlvj_jer_dn_relaxed = RooRealVar("rrv_number_dataset_signal_region"+label+"massvbf_jer_dn"+"_"+self.channel+"_mlvj_relaxed","rrv_number_dataset_signal_region"+label+"massvbf_jer_dn"+"_"+self.channel+"_mlvj_relaxed",hnum_2region_jer_dn_relaxed.GetBinContent(1));       
#        rrv_number_dataset_AllRange_mlvj_jer_dn_relaxed = RooRealVar("rrv_number_dataset_AllRange"+label+"massvbf_jer_dn"+"_"+self.channel+"_mlvj_relaxed","rrv_number_dataset_AllRange"+label+"massvbf_jer_dn"+"_"+self.channel+"_mlvj_relaxed",hnum_2region_jer_dn_relaxed.GetBinContent(2));
               
#        getattr(self.workspace4fit_,"import")(rrv_number_dataset_signal_region_mlvj_jer_dn_relaxed); rrv_number_dataset_signal_region_mlvj_jer_dn_relaxed.Print();
#        getattr(self.workspace4fit_,"import")(rrv_number_dataset_AllRange_mlvj_jer_dn_relaxed);  rrv_number_dataset_AllRange_mlvj_jer_dn_relaxed.Print();
               
        getattr(self.workspace4fit_,"import")(rdataset_sb_lo_mlvj_jer_dn); rdataset_sb_lo_mlvj_jer_dn.Print();
        getattr(self.workspace4fit_,"import")(rdataset_signal_region_mlvj_jer_dn); rdataset_signal_region_mlvj_jer_dn.Print();
        getattr(self.workspace4fit_,"import")(rdataset_sb_hi_mlvj_jer_dn); rdataset_sb_hi_mlvj_jer_dn.Print();
        getattr(self.workspace4fit_,"import")(rdataset4fit_sb_lo_mlvj_jer_dn); rdataset4fit_sb_lo_mlvj_jer_dn.Print();
        getattr(self.workspace4fit_,"import")(rdataset4fit_signal_region_mlvj_jer_dn); rdataset4fit_signal_region_mlvj_jer_dn.Print();
        getattr(self.workspace4fit_,"import")(rdataset4fit_sb_hi_mlvj_jer_dn); rdataset4fit_sb_hi_mlvj_jer_dn.Print();
        getattr(self.workspace4fit_,"import")(combData_jer_dn); combData_jer_dn.Print();
        getattr(self.workspace4fit_,"import")(combData4fit_jer_dn); combData4fit_jer_dn.Print();
#        getattr(self.workspace4fit_,"import")(rdataset_sb_lo_mlvj_jer_dn_relaxed); rdataset_sb_lo_mlvj_jer_dn_relaxed.Print();
#        getattr(self.workspace4fit_,"import")(rdataset_signal_region_mlvj_jer_dn_relaxed); rdataset_signal_region_mlvj_jer_dn_relaxed.Print();
#        getattr(self.workspace4fit_,"import")(rdataset_sb_hi_mlvj_jer_dn_relaxed); rdataset_sb_hi_mlvj_jer_dn_relaxed.Print();
#        getattr(self.workspace4fit_,"import")(rdataset4fit_sb_lo_mlvj_jer_dn_relaxed); rdataset4fit_sb_lo_mlvj_jer_dn_relaxed.Print();
#        getattr(self.workspace4fit_,"import")(rdataset4fit_signal_region_mlvj_jer_dn_relaxed); rdataset4fit_signal_region_mlvj_jer_dn_relaxed.Print();
#        getattr(self.workspace4fit_,"import")(rdataset4fit_sb_hi_mlvj_jer_dn_relaxed); rdataset4fit_sb_hi_mlvj_jer_dn_relaxed.Print();
#        getattr(self.workspace4fit_,"import")(combData_jer_dn_relaxed); combData_jer_dn_relaxed.Print();
#        getattr(self.workspace4fit_,"import")(combData4fit_jer_dn_relaxed); combData4fit_jer_dn_relaxed.Print();
          
        self.file_out.write("\n%s events number in m_lvj from dataset: %s"%(label,rdataset_signal_region_mlvj.sumEntries()))
#        self.file_out.write("\n%s events number in m_lvj from dataset relaxed: %s"%(label,rdataset_signal_region_mlvj_relaxed.sumEntries()))
                 
        #prepare m_j dataset       
        print "########### nominal value ###########";
        rrv_number_dataset_sb_lo_mj = RooRealVar("rrv_number_dataset_sb_lo"+label+"_"+self.channel+"_mj","rrv_number_dataset_sb_lo"+label+"_"+self.channel+"_mj",hnum_4region.GetBinContent(1));
        rrv_number_dataset_signal_region_mj = RooRealVar("rrv_number_dataset_signal_region"+label+"_"+self.channel+"_mj","rrv_number_dataset_signal_region"+label+"_"+self.channel+"_mj",hnum_4region.GetBinContent(2));        
        rrv_number_dataset_sb_hi_mj = RooRealVar("rrv_number_dataset_sb_hi"+label+"_"+self.channel+"_mj","rrv_number_dataset_sb_hi"+label+"_"+self.channel+"_mj",hnum_4region.GetBinContent(3));        


        getattr(self.workspace4fit_,"import")(rrv_number_dataset_sb_lo_mj); rrv_number_dataset_sb_lo_mj.Print();
        getattr(self.workspace4fit_,"import")(rrv_number_dataset_signal_region_mj); rrv_number_dataset_signal_region_mj.Print();
        getattr(self.workspace4fit_,"import")(rrv_number_dataset_sb_hi_mj); rrv_number_dataset_sb_hi_mj.Print();
        
#        rrv_number_dataset_sb_lo_mj_relaxed = RooRealVar("rrv_number_dataset_sb_lo"+label+"_"+self.channel+"_mj_relaxed","rrv_number_dataset_sb_lo"+label+"_"+self.channel+"_mj_relaxed",hnum_4region_relaxed.GetBinContent(1));
#        rrv_number_dataset_signal_region_mj_relaxed = RooRealVar("rrv_number_dataset_signal_region"+label+"_"+self.channel+"_mj_relaxed","rrv_number_dataset_signal_region"+label+"_"+self.channel+"_mj_relaxed",hnum_4region_relaxed.GetBinContent(2));        
#        rrv_number_dataset_sb_hi_mj_relaxed = RooRealVar("rrv_number_dataset_sb_hi"+label+"_"+self.channel+"_mj_relaxed","rrv_number_dataset_sb_hi"+label+"_"+self.channel+"_mj_relaxed",hnum_4region_relaxed.GetBinContent(3));

#        getattr(self.workspace4fit_,"import")(rrv_number_dataset_sb_lo_mj_relaxed); rrv_number_dataset_sb_lo_mj_relaxed.Print();
#        getattr(self.workspace4fit_,"import")(rrv_number_dataset_signal_region_mj_relaxed); rrv_number_dataset_signal_region_mj_relaxed.Print();
#        getattr(self.workspace4fit_,"import")(rrv_number_dataset_sb_hi_mj_relaxed); rrv_number_dataset_sb_hi_mj_relaxed.Print();
                

        getattr(self.workspace4fit_,"import")(rdataset_mj); rdataset_mj.Print();
        getattr(self.workspace4fit_,"import")(rdataset4fit_mj); rdataset4fit_mj.Print();
        
#        getattr(self.workspace4fit_,"import")(rdataset_mj_relaxed); rdataset_mj_relaxed.Print();
#        getattr(self.workspace4fit_,"import")(rdataset4fit_mj_relaxed); rdataset4fit_mj_relaxed.Print();

        #####jes_up
        #prepare m_j dataset       
        print "########### jes up ###########";
        rrv_number_dataset_sb_lo_mj_jes_up = RooRealVar("rrv_number_dataset_sb_lo"+label+"massvbf_jes_up"+"_"+self.channel+"_mj","rrv_number_dataset_sb_lo"+label+"massvbf_jes_up"+"_"+self.channel+"_mj",hnum_4region_jes_up.GetBinContent(1));
        rrv_number_dataset_signal_region_mj_jes_up = RooRealVar("rrv_number_dataset_signal_region"+label+"massvbf_jes_up"+"_"+self.channel+"_mj","rrv_number_dataset_signal_region"+label+"massvbf_jes_up"+"_"+self.channel+"_mj",hnum_4region_jes_up.GetBinContent(2));        
        rrv_number_dataset_sb_hi_mj_jes_up = RooRealVar("rrv_number_dataset_sb_hi"+label+"massvbf_jes_up"+"_"+self.channel+"_mj","rrv_number_dataset_sb_hi"+label+"massvbf_jes_up"+"_"+self.channel+"_mj",hnum_4region_jes_up.GetBinContent(3));        

        getattr(self.workspace4fit_,"import")(rrv_number_dataset_sb_lo_mj_jes_up); rrv_number_dataset_sb_lo_mj_jes_up.Print();
        getattr(self.workspace4fit_,"import")(rrv_number_dataset_signal_region_mj_jes_up); rrv_number_dataset_signal_region_mj_jes_up.Print();
        getattr(self.workspace4fit_,"import")(rrv_number_dataset_sb_hi_mj_jes_up); rrv_number_dataset_sb_hi_mj_jes_up.Print();
        
#        rrv_number_dataset_sb_lo_mj_jes_up_relaxed = RooRealVar("rrv_number_dataset_sb_lo"+label+"massvbf_jes_up"+"_"+self.channel+"_mj_relaxed","rrv_number_dataset_sb_lo"+label+"massvbf_jes_up"+"_"+self.channel+"_mj_relaxed",hnum_4region_jes_up_relaxed.GetBinContent(1));
#        rrv_number_dataset_signal_region_mj_jes_up_relaxed = RooRealVar("rrv_number_dataset_signal_region"+label+"massvbf_jes_up"+"_"+self.channel+"_mj_relaxed","rrv_number_dataset_signal_region"+label+"massvbf_jes_up"+"_"+self.channel+"_mj_relaxed",hnum_4region_jes_up_relaxed.GetBinContent(2));        
#        rrv_number_dataset_sb_hi_mj_jes_up_relaxed = RooRealVar("rrv_number_dataset_sb_hi"+label+"massvbf_jes_up"+"_"+self.channel+"_mj_relaxed","rrv_number_dataset_sb_hi"+label+"massvbf_jes_up"+"_"+self.channel+"_mj_relaxed",hnum_4region_jes_up_relaxed.GetBinContent(3));

#        getattr(self.workspace4fit_,"import")(rrv_number_dataset_sb_lo_mj_jes_up_relaxed); rrv_number_dataset_sb_lo_mj_jes_up_relaxed.Print();
#        getattr(self.workspace4fit_,"import")(rrv_number_dataset_signal_region_mj_jes_up_relaxed); rrv_number_dataset_signal_region_mj_jes_up_relaxed.Print();
#        getattr(self.workspace4fit_,"import")(rrv_number_dataset_sb_hi_mj_jes_up_relaxed); rrv_number_dataset_sb_hi_mj_jes_up_relaxed.Print();
                
        getattr(self.workspace4fit_,"import")(rdataset_mj_jes_up); rdataset_mj_jes_up.Print();
        getattr(self.workspace4fit_,"import")(rdataset4fit_mj_jes_up); rdataset4fit_mj_jes_up.Print();
#        getattr(self.workspace4fit_,"import")(rdataset_mj_jes_up_relaxed); rdataset_mj_jes_up_relaxed.Print();
#        getattr(self.workspace4fit_,"import")(rdataset4fit_mj_jes_up_relaxed); rdataset4fit_mj_jes_up_relaxed.Print();

        #####jes_dn

        #prepare m_j dataset       
        print "########### jes dn ###########";
        rrv_number_dataset_sb_lo_mj_jes_dn = RooRealVar("rrv_number_dataset_sb_lo"+label+"massvbf_jes_dn"+"_"+self.channel+"_mj","rrv_number_dataset_sb_lo"+label+"massvbf_jes_dn"+"_"+self.channel+"_mj",hnum_4region_jes_dn.GetBinContent(1));
        rrv_number_dataset_signal_region_mj_jes_dn = RooRealVar("rrv_number_dataset_signal_region"+label+"massvbf_jes_dn"+"_"+self.channel+"_mj","rrv_number_dataset_signal_region"+label+"massvbf_jes_dn"+"_"+self.channel+"_mj",hnum_4region_jes_dn.GetBinContent(2));        
        rrv_number_dataset_sb_hi_mj_jes_dn = RooRealVar("rrv_number_dataset_sb_hi"+label+"massvbf_jes_dn"+"_"+self.channel+"_mj","rrv_number_dataset_sb_hi"+label+"massvbf_jes_dn"+"_"+self.channel+"_mj",hnum_4region_jes_dn.GetBinContent(3));        

        getattr(self.workspace4fit_,"import")(rrv_number_dataset_sb_lo_mj_jes_dn); rrv_number_dataset_sb_lo_mj_jes_dn.Print();
        getattr(self.workspace4fit_,"import")(rrv_number_dataset_signal_region_mj_jes_dn); rrv_number_dataset_signal_region_mj_jes_dn.Print();
        getattr(self.workspace4fit_,"import")(rrv_number_dataset_sb_hi_mj_jes_dn); rrv_number_dataset_sb_hi_mj_jes_dn.Print();
        
#        rrv_number_dataset_sb_lo_mj_jes_dn_relaxed = RooRealVar("rrv_number_dataset_sb_lo"+label+"massvbf_jes_dn"+"_"+self.channel+"_mj_relaxed","rrv_number_dataset_sb_lo"+label+"massvbf_jes_dn"+"_"+self.channel+"_mj_relaxed",hnum_4region_jes_dn_relaxed.GetBinContent(1));
#        rrv_number_dataset_signal_region_mj_jes_dn_relaxed = RooRealVar("rrv_number_dataset_signal_region"+label+"massvbf_jes_dn"+"_"+self.channel+"_mj_relaxed","rrv_number_dataset_signal_region"+label+"massvbf_jes_dn"+"_"+self.channel+"_mj_relaxed",hnum_4region_jes_dn_relaxed.GetBinContent(2));        
#        rrv_number_dataset_sb_hi_mj_jes_dn_relaxed = RooRealVar("rrv_number_dataset_sb_hi"+label+"massvbf_jes_dn"+"_"+self.channel+"_mj_relaxed","rrv_number_dataset_sb_hi"+label+"massvbf_jes_dn"+"_"+self.channel+"_mj_relaxed",hnum_4region_jes_dn_relaxed.GetBinContent(3));

#        getattr(self.workspace4fit_,"import")(rrv_number_dataset_sb_lo_mj_jes_dn_relaxed); rrv_number_dataset_sb_lo_mj_jes_dn_relaxed.Print();
#        getattr(self.workspace4fit_,"import")(rrv_number_dataset_signal_region_mj_jes_dn_relaxed); rrv_number_dataset_signal_region_mj_jes_dn_relaxed.Print();
#        getattr(self.workspace4fit_,"import")(rrv_number_dataset_sb_hi_mj_jes_dn_relaxed); rrv_number_dataset_sb_hi_mj_jes_dn_relaxed.Print();
                
        getattr(self.workspace4fit_,"import")(rdataset_mj_jes_dn); rdataset_mj_jes_dn.Print();
        getattr(self.workspace4fit_,"import")(rdataset4fit_mj_jes_dn); rdataset4fit_mj_jes_dn.Print();
#        getattr(self.workspace4fit_,"import")(rdataset_mj_jes_dn_relaxed); rdataset_mj_jes_dn_relaxed.Print(); 
#        getattr(self.workspace4fit_,"import")(rdataset4fit_mj_jes_dn_relaxed); rdataset4fit_mj_jes_dn_relaxed.Print();


        #####jer

        #prepare m_j dataset       
        print "########### jer ###########";
        rrv_number_dataset_sb_lo_mj_jer = RooRealVar("rrv_number_dataset_sb_lo"+label+"massvbf_jer"+"_"+self.channel+"_mj","rrv_number_dataset_sb_lo"+label+"massvbf_jer"+"_"+self.channel+"_mj",hnum_4region_jer.GetBinContent(1));
        rrv_number_dataset_signal_region_mj_jer = RooRealVar("rrv_number_dataset_signal_region"+label+"massvbf_jer"+"_"+self.channel+"_mj","rrv_number_dataset_signal_region"+label+"massvbf_jer"+"_"+self.channel+"_mj",hnum_4region_jer.GetBinContent(2));        
        rrv_number_dataset_sb_hi_mj_jer = RooRealVar("rrv_number_dataset_sb_hi"+label+"massvbf_jer"+"_"+self.channel+"_mj","rrv_number_dataset_sb_hi"+label+"massvbf_jer"+"_"+self.channel+"_mj",hnum_4region_jer.GetBinContent(3));        

        getattr(self.workspace4fit_,"import")(rrv_number_dataset_sb_lo_mj_jer); rrv_number_dataset_sb_lo_mj_jer.Print();
        getattr(self.workspace4fit_,"import")(rrv_number_dataset_signal_region_mj_jer); rrv_number_dataset_signal_region_mj_jer.Print();
        getattr(self.workspace4fit_,"import")(rrv_number_dataset_sb_hi_mj_jer); rrv_number_dataset_sb_hi_mj_jer.Print();
        
#        rrv_number_dataset_sb_lo_mj_jer_relaxed = RooRealVar("rrv_number_dataset_sb_lo"+label+"massvbf_jer"+"_"+self.channel+"_mj_relaxed","rrv_number_dataset_sb_lo"+label+"massvbf_jer"+"_"+self.channel+"_mj_relaxed",hnum_4region_jer_relaxed.GetBinContent(1));
#        rrv_number_dataset_signal_region_mj_jer_relaxed = RooRealVar("rrv_number_dataset_signal_region"+label+"massvbf_jer"+"_"+self.channel+"_mj_relaxed","rrv_number_dataset_signal_region"+label+"massvbf_jer"+"_"+self.channel+"_mj_relaxed",hnum_4region_jer_relaxed.GetBinContent(2));        
#        rrv_number_dataset_sb_hi_mj_jer_relaxed = RooRealVar("rrv_number_dataset_sb_hi"+label+"massvbf_jer"+"_"+self.channel+"_mj_relaxed","rrv_number_dataset_sb_hi"+label+"massvbf_jer"+"_"+self.channel+"_mj_relaxed",hnum_4region_jer_relaxed.GetBinContent(3));

#        getattr(self.workspace4fit_,"import")(rrv_number_dataset_sb_lo_mj_jer_relaxed); rrv_number_dataset_sb_lo_mj_jer_relaxed.Print();
#        getattr(self.workspace4fit_,"import")(rrv_number_dataset_signal_region_mj_jer_relaxed); rrv_number_dataset_signal_region_mj_jer_relaxed.Print();
#        getattr(self.workspace4fit_,"import")(rrv_number_dataset_sb_hi_mj_jer_relaxed); rrv_number_dataset_sb_hi_mj_jer_relaxed.Print();
                
        getattr(self.workspace4fit_,"import")(rdataset_mj_jer); rdataset_mj_jer.Print();
        getattr(self.workspace4fit_,"import")(rdataset4fit_mj_jer); rdataset4fit_mj_jer.Print();
#        getattr(self.workspace4fit_,"import")(rdataset_mj_jer_relaxed); rdataset_mj_jer_relaxed.Print();
#        getattr(self.workspace4fit_,"import")(rdataset4fit_mj_jer_relaxed); rdataset4fit_mj_jer_relaxed.Print();

        #####jer_up

        #prepare m_j dataset       
        print "########### jer up ###########";
        rrv_number_dataset_sb_lo_mj_jer_up = RooRealVar("rrv_number_dataset_sb_lo"+label+"massvbf_jer_up"+"_"+self.channel+"_mj","rrv_number_dataset_sb_lo"+label+"massvbf_jer_up"+"_"+self.channel+"_mj",hnum_4region_jer_up.GetBinContent(1));
        rrv_number_dataset_signal_region_mj_jer_up = RooRealVar("rrv_number_dataset_signal_region"+label+"massvbf_jer_up"+"_"+self.channel+"_mj","rrv_number_dataset_signal_region"+label+"massvbf_jer_up"+"_"+self.channel+"_mj",hnum_4region_jer_up.GetBinContent(2));        
        rrv_number_dataset_sb_hi_mj_jer_up = RooRealVar("rrv_number_dataset_sb_hi"+label+"massvbf_jer_up"+"_"+self.channel+"_mj","rrv_number_dataset_sb_hi"+label+"massvbf_jer_up"+"_"+self.channel+"_mj",hnum_4region_jer_up.GetBinContent(3));        

        getattr(self.workspace4fit_,"import")(rrv_number_dataset_sb_lo_mj_jer_up); rrv_number_dataset_sb_lo_mj_jer_up.Print();
        getattr(self.workspace4fit_,"import")(rrv_number_dataset_signal_region_mj_jer_up); rrv_number_dataset_signal_region_mj_jer_up.Print();
        getattr(self.workspace4fit_,"import")(rrv_number_dataset_sb_hi_mj_jer_up); rrv_number_dataset_sb_hi_mj_jer_up.Print();
        
 #       rrv_number_dataset_sb_lo_mj_jer_up_relaxed = RooRealVar("rrv_number_dataset_sb_lo"+label+"massvbf_jer_up"+"_"+self.channel+"_mj_relaxed","rrv_number_dataset_sb_lo"+label+"massvbf_jer_up"+"_"+self.channel+"_mj_relaxed",hnum_4region_jer_up_relaxed.GetBinContent(1));
 #       rrv_number_dataset_signal_region_mj_jer_up_relaxed = RooRealVar("rrv_number_dataset_signal_region"+label+"massvbf_jer_up"+"_"+self.channel+"_mj_relaxed","rrv_number_dataset_signal_region"+label+"massvbf_jer_up"+"_"+self.channel+"_mj_relaxed",hnum_4region_jer_up_relaxed.GetBinContent(2));        
 #       rrv_number_dataset_sb_hi_mj_jer_up_relaxed = RooRealVar("rrv_number_dataset_sb_hi"+label+"massvbf_jer_up"+"_"+self.channel+"_mj_relaxed","rrv_number_dataset_sb_hi"+label+"massvbf_jer_up"+"_"+self.channel+"_mj_relaxed",hnum_4region_jer_up_relaxed.GetBinContent(3));

 #       getattr(self.workspace4fit_,"import")(rrv_number_dataset_sb_lo_mj_jer_up_relaxed); rrv_number_dataset_sb_lo_mj_jer_up_relaxed.Print();
 #       getattr(self.workspace4fit_,"import")(rrv_number_dataset_signal_region_mj_jer_up_relaxed); rrv_number_dataset_signal_region_mj_jer_up_relaxed.Print();
 #       getattr(self.workspace4fit_,"import")(rrv_number_dataset_sb_hi_mj_jer_up_relaxed); rrv_number_dataset_sb_hi_mj_jer_up_relaxed.Print();
                
        getattr(self.workspace4fit_,"import")(rdataset_mj_jer_up); rdataset_mj_jer_up.Print();
        getattr(self.workspace4fit_,"import")(rdataset4fit_mj_jer_up); rdataset4fit_mj_jer_up.Print();
 #       getattr(self.workspace4fit_,"import")(rdataset_mj_jer_up_relaxed); rdataset_mj_jer_up_relaxed.Print();
 #       getattr(self.workspace4fit_,"import")(rdataset4fit_mj_jer_up_relaxed); rdataset4fit_mj_jer_up_relaxed.Print();

        #####jer_dn

        #prepare m_j dataset       
        print "########### jer dn ###########";
        rrv_number_dataset_sb_lo_mj_jer_dn = RooRealVar("rrv_number_dataset_sb_lo"+label+"massvbf_jer_dn"+"_"+self.channel+"_mj","rrv_number_dataset_sb_lo"+label+"massvbf_jer_dn"+"_"+self.channel+"_mj",hnum_4region_jer_dn.GetBinContent(1));
        rrv_number_dataset_signal_region_mj_jer_dn = RooRealVar("rrv_number_dataset_signal_region"+label+"massvbf_jer_dn"+"_"+self.channel+"_mj","rrv_number_dataset_signal_region"+label+"massvbf_jer_dn"+"_"+self.channel+"_mj",hnum_4region_jer_dn.GetBinContent(2));        
        rrv_number_dataset_sb_hi_mj_jer_dn = RooRealVar("rrv_number_dataset_sb_hi"+label+"massvbf_jer_dn"+"_"+self.channel+"_mj","rrv_number_dataset_sb_hi"+label+"massvbf_jer_dn"+"_"+self.channel+"_mj",hnum_4region_jer_dn.GetBinContent(3));        

        getattr(self.workspace4fit_,"import")(rrv_number_dataset_sb_lo_mj_jer_dn); rrv_number_dataset_sb_lo_mj_jer_dn.Print();
        getattr(self.workspace4fit_,"import")(rrv_number_dataset_signal_region_mj_jer_dn); rrv_number_dataset_signal_region_mj_jer_dn.Print();
        getattr(self.workspace4fit_,"import")(rrv_number_dataset_sb_hi_mj_jer_dn); rrv_number_dataset_sb_hi_mj_jer_dn.Print();
        
 #       rrv_number_dataset_sb_lo_mj_jer_dn_relaxed = RooRealVar("rrv_number_dataset_sb_lo"+label+"massvbf_jer_dn"+"_"+self.channel+"_mj_relaxed","rrv_number_dataset_sb_lo"+label+"massvbf_jer_dn"+"_"+self.channel+"_mj_relaxed",hnum_4region_jer_dn_relaxed.GetBinContent(1));
 #       rrv_number_dataset_signal_region_mj_jer_dn_relaxed = RooRealVar("rrv_number_dataset_signal_region"+label+"massvbf_jer_dn"+"_"+self.channel+"_mj_relaxed","rrv_number_dataset_signal_region"+label+"massvbf_jer_dn"+"_"+self.channel+"_mj_relaxed",hnum_4region_jer_dn_relaxed.GetBinContent(2));        
 #       rrv_number_dataset_sb_hi_mj_jer_dn_relaxed = RooRealVar("rrv_number_dataset_sb_hi"+label+"massvbf_jer_dn"+"_"+self.channel+"_mj_relaxed","rrv_number_dataset_sb_hi"+label+"massvbf_jer_dn"+"_"+self.channel+"_mj_relaxed",hnum_4region_jer_dn_relaxed.GetBinContent(3));

 #       getattr(self.workspace4fit_,"import")(rrv_number_dataset_sb_lo_mj_jer_dn_relaxed); rrv_number_dataset_sb_lo_mj_jer_dn_relaxed.Print();
 #       getattr(self.workspace4fit_,"import")(rrv_number_dataset_signal_region_mj_jer_dn_relaxed); rrv_number_dataset_signal_region_mj_jer_dn_relaxed.Print();
 #       getattr(self.workspace4fit_,"import")(rrv_number_dataset_sb_hi_mj_jer_dn_relaxed); rrv_number_dataset_sb_hi_mj_jer_dn_relaxed.Print();
                
        getattr(self.workspace4fit_,"import")(rdataset_mj_jer_dn); rdataset_mj_jer_dn.Print();
        getattr(self.workspace4fit_,"import")(rdataset4fit_mj_jer_dn); rdataset4fit_mj_jer_dn.Print();
 #       getattr(self.workspace4fit_,"import")(rdataset_mj_jer_dn_relaxed); rdataset_mj_jer_dn_relaxed.Print();
 #       getattr(self.workspace4fit_,"import")(rdataset4fit_mj_jer_dn_relaxed); rdataset4fit_mj_jer_dn_relaxed.Print();
                 

        
    ##### Prepare the workspace for the limit and to store info to be printed in the datacard
    def prepare_limit(self,mode,useRelaxedShape = 0, isTTbarFloating=0, isVVFloating=0, isSTopFloating=0, isWW_EWKFloating=0):

        print "####################### prepare_limit for %s method ####################"%(mode);

        getattr(self.workspace4limit_,"import")(self.workspace4fit_.var("rrv_mass_lvj"));

        ### whole number of events from the considered signal sample, WJets, VV, TTbar, STop -> counting experiment
        getattr(self.workspace4limit_,"import")(self.workspace4fit_.var("rrv_number_fitting_signal_region_%s_%s_mlvj"%(self.higgs_sample,self.channel)).clone("rate_%s_for_counting"%(self.higgs_sample) ) )
        getattr(self.workspace4limit_,"import")(self.workspace4fit_.var("rrv_number_fitting_signal_region_%s_%s_mlvj"%(self.vbfhiggs_sample,self.channel)).clone("rate_%s_for_counting"%(self.vbfhiggs_sample) ) )

        getattr(self.workspace4limit_,"import")(self.workspace4fit_.var("rrv_number_fitting_signal_region_WJets0_%s_mlvj"%(self.channel)).clone("rate_WJets_for_counting"))
        getattr(self.workspace4limit_,"import")(self.workspace4fit_.var("rrv_number_fitting_signal_region_VV_%s_mlvj"%(self.channel)).clone("rate_VV_for_counting"))
        getattr(self.workspace4limit_,"import")(self.workspace4fit_.var("rrv_number_fitting_signal_region_WW_EWK_%s_mlvj"%(self.channel)).clone("rate_WW_EWK_for_counting"))        
        getattr(self.workspace4limit_,"import")(self.workspace4fit_.var("rrv_number_fitting_signal_region_TTbar_%s_mlvj"%(self.channel)).clone("rate_TTbar_for_counting"))
        getattr(self.workspace4limit_,"import")(self.workspace4fit_.var("rrv_number_fitting_signal_region_STop_%s_mlvj"%(self.channel)).clone("rate_STop_for_counting"))


        ### number of signal, Wjets, VV, TTbar and STop --> unbinned shape analysis             
        getattr(self.workspace4limit_,"import")(self.workspace4fit_.var("rrv_number_%s_signal_region_%s_mlvj"%(self.higgs_sample, self.channel)).clone("rate_%s_for_unbin"%(self.higgs_sample)));
        getattr(self.workspace4limit_,"import")(self.workspace4fit_.var("rrv_number_%s_signal_region_%s_mlvj"%(self.vbfhiggs_sample, self.channel)).clone("rate_%s_for_unbin"%(self.vbfhiggs_sample)));

        getattr(self.workspace4limit_,"import")(self.workspace4fit_.var("rrv_number_WJets0_signal_region_%s_mlvj"%(self.channel)).clone("rate_WJets_for_unbin"));
        getattr(self.workspace4limit_,"import")(self.workspace4fit_.var("rrv_number_VV_signal_region_%s_mlvj"%(self.channel)).clone("rate_VV_for_unbin"));
        getattr(self.workspace4limit_,"import")(self.workspace4fit_.var("rrv_number_WW_EWK_signal_region_%s_mlvj"%(self.channel)).clone("rate_WW_EWK_for_unbin"));        
        getattr(self.workspace4limit_,"import")(self.workspace4fit_.var("rrv_number_TTbar_signal_region_%s_mlvj"%(self.channel)).clone("rate_TTbar_for_unbin"));
        getattr(self.workspace4limit_,"import")(self.workspace4fit_.var("rrv_number_STop_signal_region_%s_mlvj"%(self.channel)).clone("rate_STop_for_unbin"));

        ### Set the error properly -> taking into account lumi, Vtagger and theoretical uncertainty on XS -> for VV, TTbar and STop
        self.workspace4limit_.var("rate_VV_for_unbin").setError(self.workspace4limit_.var("rate_VV_for_unbin").getVal()*TMath.Sqrt(self.lumi_uncertainty*self.lumi_uncertainty+self.rrv_wtagger_eff_reweight_forV.getError()/self.rrv_wtagger_eff_reweight_forV.getVal()*self.rrv_wtagger_eff_reweight_forV.getError()/self.rrv_wtagger_eff_reweight_forV.getVal()+self.XS_VV_uncertainty*self.XS_VV_uncertainty));
        self.workspace4limit_.var("rate_WW_EWK_for_unbin").setError(self.workspace4limit_.var("rate_WW_EWK_for_unbin").getVal()*TMath.Sqrt(self.lumi_uncertainty*self.lumi_uncertainty+self.rrv_wtagger_eff_reweight_forV.getError()/self.rrv_wtagger_eff_reweight_forV.getVal()*self.rrv_wtagger_eff_reweight_forV.getError()/self.rrv_wtagger_eff_reweight_forV.getVal()+self.XS_VV_uncertainty*self.XS_VV_uncertainty));        
        self.workspace4limit_.var("rate_STop_for_unbin").setError(self.workspace4limit_.var("rate_STop_for_unbin").getVal()*TMath.Sqrt(self.lumi_uncertainty*self.lumi_uncertainty+self.rrv_wtagger_eff_reweight_forT.getError()/self.rrv_wtagger_eff_reweight_forT.getVal()*self.rrv_wtagger_eff_reweight_forT.getError()/self.rrv_wtagger_eff_reweight_forT.getVal()+self.XS_STop_uncertainty*self.XS_STop_uncertainty));
        self.workspace4limit_.var("rate_TTbar_for_unbin").setError(self.workspace4limit_.var("rate_TTbar_for_unbin").getVal()*TMath.Sqrt( self.lumi_uncertainty*self.lumi_uncertainty  + self.rrv_wtagger_eff_reweight_forT.getError()/self.rrv_wtagger_eff_reweight_forT.getVal()*self.rrv_wtagger_eff_reweight_forT.getError()/self.rrv_wtagger_eff_reweight_forT.getVal()));



        if mode=="sideband_correction_method1":
            
         getattr(self.workspace4limit_,"import")(self.workspace4fit_.pdf("model_pdf_WJets0_signal_region_%s_after_correct_mlvj"%(self.channel)).clone("WJets_%s"%(self.channel)));
         self.workspace4limit_.allVars().Print();

        if isTTbarFloating:
         if useRelaxedShape == 1 :   
          getattr(self.workspace4limit_,"import")(self.workspace4fit_.pdf("model_pdf_TTbar_signal_region_%s_mlvj_relaxed_Deco_TTbar_signal_region_%s_%s_mlvj_relaxed"%(self.channel, self.channel, self.wtagger_label)).clone("TTbar_%s"%(self.channel)));
         else: 
          getattr(self.workspace4limit_,"import")(self.workspace4fit_.pdf("model_pdf_TTbar_signal_region_%s_mlvj_Deco_TTbar_signal_region_%s_%s_mlvj"%(self.channel, self.channel, self.wtagger_label)).clone("TTbar_%s"%(self.channel)));
        else :
         if useRelaxedShape == 1 :
          getattr(self.workspace4limit_,"import")(self.workspace4fit_.pdf("model_pdf_TTbar_signal_region_%s_mlvj_relaxed"%(self.channel)).clone("TTbar_%s"%(self.channel)))
         else:    
          getattr(self.workspace4limit_,"import")(self.workspace4fit_.pdf("model_pdf_TTbar_signal_region_%s_mlvj"%(self.channel)).clone("TTbar_%s"%(self.channel)))

        if isSTopFloating :
         if useRelaxedShape == 1 :
          getattr(self.workspace4limit_,"import")(self.workspace4fit_.pdf("model_pdf_STop_signal_region_%s_mlvj_relaxed_Deco_STop_signal_region_%s_%s_mlvj_relaxed"%(self.channel, self.channel, self.wtagger_label)).clone("STop_%s"%(self.channel)))
         else:
          getattr(self.workspace4limit_,"import")(self.workspace4fit_.pdf("model_pdf_STop_signal_region_%s_mlvj_Deco_STop_signal_region_%s_%s_mlvj"%(self.channel, self.channel, self.wtagger_label)).clone("STop_%s"%(self.channel)))   
        else :
         if useRelaxedShape == 1 :
          getattr(self.workspace4limit_,"import")(self.workspace4fit_.pdf("model_pdf_STop_signal_region_%s_mlvj_relaxed"%(self.channel)).clone("STop_%s"%(self.channel)))
         else: 
          getattr(self.workspace4limit_,"import")(self.workspace4fit_.pdf("model_pdf_STop_signal_region_%s_mlvj"%(self.channel)).clone("STop_%s"%(self.channel)))

        if isVVFloating :
         if useRelaxedShape == 1:   
          getattr(self.workspace4limit_,"import")(self.workspace4fit_.pdf("model_pdf_VV_signal_region_%s_mlvj_relaxed_Deco_VV_signal_region_%s_%s_mlvj_relaxed"%(self.channel, self.channel, self.wtagger_label)).clone("VV_%s"%(self.channel)))
         else:
          getattr(self.workspace4limit_,"import")(self.workspace4fit_.pdf("model_pdf_VV_signal_region_%s_mlvj_Deco_VV_signal_region_%s_%s_mlvj"%(self.channel, self.channel, self.wtagger_label)).clone("VV_%s"%(self.channel)))
        else:
         if useRelaxedShape == 1:   
          getattr(self.workspace4limit_,"import")(self.workspace4fit_.pdf("model_pdf_VV_signal_region_%s_mlvj_relaxed"%(self.channel)).clone("VV_%s"%(self.channel)))
         else:
          getattr(self.workspace4limit_,"import")(self.workspace4fit_.pdf("model_pdf_VV_signal_region_%s_mlvj"%(self.channel)).clone("VV_%s"%(self.channel)))
             
        if isWW_EWKFloating :
         if useRelaxedShape == 1:  
          getattr(self.workspace4limit_,"import")(self.workspace4fit_.pdf("model_pdf_WW_EWK_signal_region_%s_mlvj_relaxed_Deco_WW_EWK_signal_region_%s_%s_mlvj_relaxed"%(self.channel, self.channel, self.wtagger_label)).clone("WW_EWK_%s"%(self.channel)))
         else:
          getattr(self.workspace4limit_,"import")(self.workspace4fit_.pdf("model_pdf_WW_EWK_signal_region_%s_mlvj_Deco_WW_EWK_signal_region_%s_%s_mlvj"%(self.channel, self.channel, self.wtagger_label)).clone("WW_EWK_%s"%(self.channel)))             
        else:
         if useRelaxedShape == 1:  
          getattr(self.workspace4limit_,"import")(self.workspace4fit_.pdf("model_pdf_WW_EWK_signal_region_%s_mlvj_relaxed"%(self.channel)).clone("WW_EWK_%s"%(self.channel)));         
         else:                                                              
          getattr(self.workspace4limit_,"import")(self.workspace4fit_.pdf("model_pdf_WW_EWK_signal_region_%s_mlvj"%(self.channel)).clone("WW_EWK_%s"%(self.channel)));         


### signal shape
        getattr(self.workspace4limit_,"import")(self.workspace4fit_.pdf("model_pdf_%s_signal_region_%s_mlvj"%(self.higgs_sample,self.channel)).clone(self.higgs_sample+"_%s"%(self.channel)))
        getattr(self.workspace4limit_,"import")(self.workspace4fit_.pdf("model_pdf_%s_signal_region_%s_mlvj"%(self.vbfhiggs_sample,self.channel)).clone(self.vbfhiggs_sample+"_%s"%(self.channel)))




###create "fake data" for the limit
        rrv_x = self.workspace4limit_.var("rrv_mass_lvj")
        data_obs = self.workspace4fit_.data("rdataset_data_signal_region_%s_mlvj"%(self.channel))
        model_pdf_ggH   = self.workspace4limit_.pdf("%s_%s"%(self.higgs_sample,self.channel))
        model_pdf_vbfH  = self.workspace4limit_.pdf("%s_%s"%(self.vbfhiggs_sample,self.channel))
        model_pdf_WJets = self.workspace4limit_.pdf("WJets_%s"%(self.channel))
        model_pdf_VV = self.workspace4limit_.pdf("VV_%s"%(self.channel))
        model_pdf_WW_EWK = self.workspace4limit_.pdf("WW_EWK_%s"%(self.channel))
        model_pdf_TTbar = self.workspace4limit_.pdf("TTbar_%s"%(self.channel))
        model_pdf_STop  = self.workspace4limit_.pdf("STop_%s"%(self.channel))

        rrv_number_ggH = self.workspace4limit_.var("rate_%s_for_unbin"%(self.higgs_sample))
        rrv_number_vbfH = self.workspace4limit_.var("rate_%s_for_unbin"%(self.vbfhiggs_sample))
        rrv_number_WJets = self.workspace4limit_.var("rate_WJets_for_unbin")
        rrv_number_VV = self.workspace4limit_.var("rate_VV_for_unbin")
        rrv_number_WW_EWK = self.workspace4limit_.var("rate_WW_EWK_for_unbin")        
        rrv_number_TTbar = self.workspace4limit_.var("rate_TTbar_for_unbin")
        rrv_number_STop = self.workspace4limit_.var("rate_STop_for_unbin")

        rrv_number_Total_background_MC = RooRealVar("rrv_number_Total_background_MC","rrv_number_Total_background_MC",
                rrv_number_WJets.getVal()+
                rrv_number_VV.getVal()+
                rrv_number_WW_EWK.getVal()+                                                    
                rrv_number_TTbar.getVal()+
                rrv_number_STop.getVal());
        rrv_number_Total_background_MC.setError(TMath.Sqrt(
                rrv_number_WJets.getError()* rrv_number_WJets.getError()+
                rrv_number_VV.getError()* rrv_number_VV.getError()+
                rrv_number_WW_EWK.getError()* rrv_number_WW_EWK.getError()+                
                rrv_number_TTbar.getError()* rrv_number_TTbar.getError()+
                rrv_number_STop.getError() *rrv_number_STop.getError() 
                ));


        model_Total_background_MC = RooAddPdf("model_Total_background_MC","model_Total_background_MC",RooArgList(model_pdf_WJets,model_pdf_VV,model_pdf_WW_EWK,model_pdf_TTbar,model_pdf_STop),RooArgList(rrv_number_WJets,rrv_number_VV,rrv_number_WW_EWK,rrv_number_TTbar,rrv_number_STop));


        new_data_obs = model_Total_background_MC.generate(RooArgSet(rrv_x),int(data_obs.sumEntries()) );
        new_data_obs.Print();        

        if options.pseudodata == 0:
          getattr(self.workspace4limit_,"import")(self.workspace4fit_.data("rdataset_data_signal_region_%s_mlvj"%(self.channel)).Clone("data_obs_%s"%(self.channel)))
        else:
          getattr(self.workspace4limit_,"import")(new_data_obs.Clone("data_obs_%s"%(self.channel)))            




        ### Fix all the Pdf parameters             
#        rrv_x = self.workspace4limit_.var("rrv_mass_lvj");

        self.fix_Pdf(self.workspace4limit_.pdf("TTbar_%s"%(self.channel)), RooArgSet(rrv_x) ); 
        self.fix_Pdf(self.workspace4limit_.pdf("STop_%s"%(self.channel)), RooArgSet(rrv_x)); 
        self.fix_Pdf(self.workspace4limit_.pdf("VV_%s"%(self.channel)), RooArgSet(rrv_x));
        self.fix_Pdf(self.workspace4limit_.pdf("WW_EWK_%s"%(self.channel)), RooArgSet(rrv_x));         
        self.fix_Pdf(self.workspace4limit_.pdf("WJets_%s"%(self.channel)), RooArgSet(rrv_x)); 

        print " ############## Workspace for limit ";
        parameters_workspace = self.workspace4limit_.allVars();
        par = parameters_workspace.createIterator();
        par.Reset();
        param = par.Next()
        while (param):
         param.Print();
         param = par.Next()
        self.workspace4limit_.Print()

        params_list=[];
        ### main modality for the alpha function method
        if mode=="sideband_correction_method1":

            if self.MODEL_4_mlvj == "ErfExp_v1" or self.MODEL_4_mlvj == "ErfPow_v1" or self.MODEL_4_mlvj == "2Exp" :
                ### uncertainty inflation on the Wjets shape from fitting data in sb_lo
                self.workspace4limit_.var("Deco_WJets0_sb_lo_from_fitting_%s_%s_mlvj_eig0"%(self.channel, self.wtagger_label)).setError(self.shape_para_error_WJets0);
                self.workspace4limit_.var("Deco_WJets0_sb_lo_from_fitting_%s_%s_mlvj_eig1"%(self.channel, self.wtagger_label)).setError(self.shape_para_error_WJets0);
                self.workspace4limit_.var("Deco_WJets0_sb_lo_from_fitting_%s_%s_mlvj_eig2"%(self.channel, self.wtagger_label)).setError(self.shape_para_error_WJets0);
                self.workspace4limit_.var("Deco_WJets0_sb_lo_from_fitting_%s_%s_mlvj_eig3"%(self.channel, self.wtagger_label)).setError(self.shape_para_error_WJets0);
                ### Add to the parameter list
                params_list.append(self.workspace4limit_.var("Deco_WJets0_sb_lo_from_fitting_%s_%s_mlvj_eig0"%(self.channel, self.wtagger_label)));
                params_list.append(self.workspace4limit_.var("Deco_WJets0_sb_lo_from_fitting_%s_%s_mlvj_eig1"%(self.channel, self.wtagger_label)));
                params_list.append(self.workspace4limit_.var("Deco_WJets0_sb_lo_from_fitting_%s_%s_mlvj_eig2"%(self.channel, self.wtagger_label)));
                params_list.append(self.workspace4limit_.var("Deco_WJets0_sb_lo_from_fitting_%s_%s_mlvj_eig3"%(self.channel, self.wtagger_label)));

                ### Do the same for alpha paramter
                self.workspace4limit_.var("Deco_WJets0_sim_%s_%s_mlvj_eig0"%(self.channel, self.wtagger_label)).setError(self.shape_para_error_alpha);
                self.workspace4limit_.var("Deco_WJets0_sim_%s_%s_mlvj_eig1"%(self.channel, self.wtagger_label)).setError(self.shape_para_error_alpha);
                self.workspace4limit_.var("Deco_WJets0_sim_%s_%s_mlvj_eig2"%(self.channel, self.wtagger_label)).setError(self.shape_para_error_alpha);
                self.workspace4limit_.var("Deco_WJets0_sim_%s_%s_mlvj_eig3"%(self.channel, self.wtagger_label)).setError(self.shape_para_error_alpha);
                self.workspace4limit_.var("Deco_WJets0_sim_%s_%s_mlvj_eig4"%(self.channel, self.wtagger_label)).setError(self.shape_para_error_alpha);
                self.workspace4limit_.var("Deco_WJets0_sim_%s_%s_mlvj_eig5"%(self.channel, self.wtagger_label)).setError(self.shape_para_error_alpha);
                ### Add to the parameter list
                params_list.append(self.workspace4limit_.var("Deco_WJets0_sim_%s_%s_mlvj_eig0"%(self.channel, self.wtagger_label)))
                params_list.append(self.workspace4limit_.var("Deco_WJets0_sim_%s_%s_mlvj_eig1"%(self.channel, self.wtagger_label)))
                params_list.append(self.workspace4limit_.var("Deco_WJets0_sim_%s_%s_mlvj_eig2"%(self.channel, self.wtagger_label)))
                params_list.append(self.workspace4limit_.var("Deco_WJets0_sim_%s_%s_mlvj_eig3"%(self.channel, self.wtagger_label)))
                params_list.append(self.workspace4limit_.var("Deco_WJets0_sim_%s_%s_mlvj_eig4"%(self.channel, self.wtagger_label)))
                params_list.append(self.workspace4limit_.var("Deco_WJets0_sim_%s_%s_mlvj_eig5"%(self.channel, self.wtagger_label)))

                ### Do the same for the TTbar
                if isTTbarFloating !=0:
                  if useRelaxedShape == 1 :
                    self.workspace4limit_.var("Deco_TTbar_signal_region_%s_%s_mlvj_relaxed_eig0"%(self.channel, self.wtagger_label)).setError(self.shape_para_error_TTbar);
                    self.workspace4limit_.var("Deco_TTbar_signal_region_%s_%s_mlvj_relaxed_eig1"%(self.channel, self.wtagger_label)).setError(self.shape_para_error_TTbar);
                    self.workspace4limit_.var("Deco_TTbar_signal_region_%s_%s_mlvj_relaxed_eig2"%(self.channel, self.wtagger_label)).setError(self.shape_para_error_TTbar);

                    params_list.append(self.workspace4limit_.var("Deco_TTbar_signal_region_%s_%s_mlvj_relaxed_eig0"%(self.channel, self.wtagger_label)));
                    params_list.append(self.workspace4limit_.var("Deco_TTbar_signal_region_%s_%s_mlvj_relaxed_eig1"%(self.channel, self.wtagger_label)));
                    params_list.append(self.workspace4limit_.var("Deco_TTbar_signal_region_%s_%s_mlvj_relaxed_eig2"%(self.channel, self.wtagger_label)));
                  else:
                    self.workspace4limit_.var("Deco_TTbar_signal_region_%s_%s_mlvj_eig0"%(self.channel, self.wtagger_label)).setError(self.shape_para_error_TTbar);
                    self.workspace4limit_.var("Deco_TTbar_signal_region_%s_%s_mlvj_eig1"%(self.channel, self.wtagger_label)).setError(self.shape_para_error_TTbar);
                    self.workspace4limit_.var("Deco_TTbar_signal_region_%s_%s_mlvj_eig2"%(self.channel, self.wtagger_label)).setError(self.shape_para_error_TTbar);

                    params_list.append(self.workspace4limit_.var("Deco_TTbar_signal_region_%s_%s_mlvj_eig0"%(self.channel, self.wtagger_label)));
                    params_list.append(self.workspace4limit_.var("Deco_TTbar_signal_region_%s_%s_mlvj_eig1"%(self.channel, self.wtagger_label)));
                    params_list.append(self.workspace4limit_.var("Deco_TTbar_signal_region_%s_%s_mlvj_eig2"%(self.channel, self.wtagger_label)));

            if self.MODEL_4_mlvj=="ErfPow2_v1" or self.MODEL_4_mlvj=="ErfPowExp_v1" :
                self.workspace4limit_.var("Deco_WJets0_sb_lo_from_fitting_%s_%s_mlvj_eig0"%(self.channel, self.wtagger_label)).setError(self.shape_para_error_WJets0);
                self.workspace4limit_.var("Deco_WJets0_sb_lo_from_fitting_%s_%s_mlvj_eig1"%(self.channel, self.wtagger_label)).setError(self.shape_para_error_WJets0);
                self.workspace4limit_.var("Deco_WJets0_sb_lo_from_fitting_%s_%s_mlvj_eig2"%(self.channel, self.wtagger_label)).setError(self.shape_para_error_WJets0);
                self.workspace4limit_.var("Deco_WJets0_sb_lo_from_fitting_%s_%s_mlvj_eig3"%(self.channel, self.wtagger_label)).setError(self.shape_para_error_WJets0);
                self.workspace4limit_.var("Deco_WJets0_sb_lo_from_fitting_%s_%s_mlvj_eig4"%(self.channel, self.wtagger_label)).setError(self.shape_para_error_WJets0);

                params_list.append(self.workspace4limit_.var("Deco_WJets0_sb_lo_from_fitting_%s_%s_mlvj_eig0"%(self.channel, self.wtagger_label)));
                params_list.append(self.workspace4limit_.var("Deco_WJets0_sb_lo_from_fitting_%s_%s_mlvj_eig1"%(self.channel, self.wtagger_label)));
                params_list.append(self.workspace4limit_.var("Deco_WJets0_sb_lo_from_fitting_%s_%s_mlvj_eig2"%(self.channel, self.wtagger_label)));
                params_list.append(self.workspace4limit_.var("Deco_WJets0_sb_lo_from_fitting_%s_%s_mlvj_eig3"%(self.channel, self.wtagger_label)));
                params_list.append(self.workspace4limit_.var("Deco_WJets0_sb_lo_from_fitting_%s_%s_mlvj_eig4"%(self.channel, self.wtagger_label)));

                self.workspace4limit_.var("Deco_WJets0_sim_%s_%s_mlvj_eig0"%(self.channel, self.wtagger_label)).setError(self.shape_para_error_alpha);
                self.workspace4limit_.var("Deco_WJets0_sim_%s_%s_mlvj_eig1"%(self.channel, self.wtagger_label)).setError(self.shape_para_error_alpha);
                self.workspace4limit_.var("Deco_WJets0_sim_%s_%s_mlvj_eig2"%(self.channel, self.wtagger_label)).setError(self.shape_para_error_alpha);
                self.workspace4limit_.var("Deco_WJets0_sim_%s_%s_mlvj_eig3"%(self.channel, self.wtagger_label)).setError(self.shape_para_error_alpha);
                self.workspace4limit_.var("Deco_WJets0_sim_%s_%s_mlvj_eig4"%(self.channel, self.wtagger_label)).setError(self.shape_para_error_alpha);
                self.workspace4limit_.var("Deco_WJets0_sim_%s_%s_mlvj_eig5"%(self.channel, self.wtagger_label)).setError(self.shape_para_error_alpha);
                self.workspace4limit_.var("Deco_WJets0_sim_%s_%s_mlvj_eig6"%(self.channel, self.wtagger_label)).setError(self.shape_para_error_alpha);
                self.workspace4limit_.var("Deco_WJets0_sim_%s_%s_mlvj_eig7"%(self.channel, self.wtagger_label)).setError(self.shape_para_error_alpha);

                params_list.append(self.workspace4limit_.var("Deco_WJets0_sim_%s_%s_mlvj_eig0"%(self.channel, self.wtagger_label)))
                params_list.append(self.workspace4limit_.var("Deco_WJets0_sim_%s_%s_mlvj_eig1"%(self.channel, self.wtagger_label)))
                params_list.append(self.workspace4limit_.var("Deco_WJets0_sim_%s_%s_mlvj_eig2"%(self.channel, self.wtagger_label)))
                params_list.append(self.workspace4limit_.var("Deco_WJets0_sim_%s_%s_mlvj_eig3"%(self.channel, self.wtagger_label)))
                params_list.append(self.workspace4limit_.var("Deco_WJets0_sim_%s_%s_mlvj_eig4"%(self.channel, self.wtagger_label)))
                params_list.append(self.workspace4limit_.var("Deco_WJets0_sim_%s_%s_mlvj_eig5"%(self.channel, self.wtagger_label)))
                params_list.append(self.workspace4limit_.var("Deco_WJets0_sim_%s_%s_mlvj_eig6"%(self.channel, self.wtagger_label)))
                params_list.append(self.workspace4limit_.var("Deco_WJets0_sim_%s_%s_mlvj_eig7"%(self.channel, self.wtagger_label)))


                if isTTbarFloating !=0 :
                  if useRelaxedShape == 1:  
                    self.workspace4limit_.var("Deco_TTbar_signal_region_%s_%s_mlvj_relaxed_eig0"%(self.channel, self.wtagger_label)).setError(self.shape_para_error_TTbar);
                    self.workspace4limit_.var("Deco_TTbar_signal_region_%s_%s_mlvj_relaxed_eig1"%(self.channel, self.wtagger_label)).setError(self.shape_para_error_TTbar);
                    self.workspace4limit_.var("Deco_TTbar_signal_region_%s_%s_mlvj_relaxed_eig2"%(self.channel, self.wtagger_label)).setError(self.shape_para_error_TTbar);
                    self.workspace4limit_.var("Deco_TTbar_signal_region_%s_%s_mlvj_relaxed_eig3"%(self.channel, self.wtagger_label)).setError(self.shape_para_error_TTbar);

                    params_list.append(self.workspace4limit_.var("Deco_TTbar_signal_region_%s_%s_mlvj_relaxed_eig0"%(self.channel, self.wtagger_label)));
                    params_list.append(self.workspace4limit_.var("Deco_TTbar_signal_region_%s_%s_mlvj_relaxed_eig1"%(self.channel, self.wtagger_label)));
                    params_list.append(self.workspace4limit_.var("Deco_TTbar_signal_region_%s_%s_mlvj_relaxed_eig2"%(self.channel, self.wtagger_label)));
                    params_list.append(self.workspace4limit_.var("Deco_TTbar_signal_region_%s_%s_mlvj_relaxed_eig3"%(self.channel, self.wtagger_label)));
                  else:
                    self.workspace4limit_.var("Deco_TTbar_signal_region_%s_%s_mlvj_eig0"%(self.channel, self.wtagger_label)).setError(self.shape_para_error_TTbar);
                    self.workspace4limit_.var("Deco_TTbar_signal_region_%s_%s_mlvj_eig1"%(self.channel, self.wtagger_label)).setError(self.shape_para_error_TTbar);
                    self.workspace4limit_.var("Deco_TTbar_signal_region_%s_%s_mlvj_eig2"%(self.channel, self.wtagger_label)).setError(self.shape_para_error_TTbar);
                    self.workspace4limit_.var("Deco_TTbar_signal_region_%s_%s_mlvj_eig3"%(self.channel, self.wtagger_label)).setError(self.shape_para_error_TTbar);

                    params_list.append(self.workspace4limit_.var("Deco_TTbar_signal_region_%s_%s_mlvj_eig0"%(self.channel, self.wtagger_label)));
                    params_list.append(self.workspace4limit_.var("Deco_TTbar_signal_region_%s_%s_mlvj_eig1"%(self.channel, self.wtagger_label)));
                    params_list.append(self.workspace4limit_.var("Deco_TTbar_signal_region_%s_%s_mlvj_eig2"%(self.channel, self.wtagger_label)));
                    params_list.append(self.workspace4limit_.var("Deco_TTbar_signal_region_%s_%s_mlvj_eig3"%(self.channel, self.wtagger_label)));

            if self.MODEL_4_mlvj=="Exp" or self.MODEL_4_mlvj=="Pow" :

                self.workspace4limit_.var("Deco_WJets0_sb_lo_from_fitting_%s_%s_mlvj_eig0"%(self.channel, self.wtagger_label)).setError(self.shape_para_error_WJets0);
                self.workspace4limit_.var("Deco_WJets0_sb_lo_from_fitting_%s_%s_mlvj_eig1"%(self.channel, self.wtagger_label)).setError(self.shape_para_error_WJets0);

                params_list.append(self.workspace4limit_.var("Deco_WJets0_sb_lo_from_fitting_%s_%s_mlvj_eig0"%(self.channel, self.wtagger_label)));
                params_list.append(self.workspace4limit_.var("Deco_WJets0_sb_lo_from_fitting_%s_%s_mlvj_eig1"%(self.channel, self.wtagger_label)));

                
                self.workspace4limit_.var("Deco_WJets0_sim_%s_%s_mlvj_eig0"%(self.channel, self.wtagger_label)).setError(self.shape_para_error_alpha);
                self.workspace4limit_.var("Deco_WJets0_sim_%s_%s_mlvj_eig1"%(self.channel, self.wtagger_label)).setError(self.shape_para_error_alpha);

                params_list.append(self.workspace4limit_.var("Deco_WJets0_sim_%s_%s_mlvj_eig0"%(self.channel, self.wtagger_label)))
                params_list.append(self.workspace4limit_.var("Deco_WJets0_sim_%s_%s_mlvj_eig1"%(self.channel, self.wtagger_label)))

                if isTTbarFloating !=0 :
                 if useRelaxedShape == 1:
                  self.workspace4limit_.var("Deco_TTbar_signal_region_%s_%s_mlvj_relaxed_eig0"%(self.channel, self.wtagger_label)).setError(self.shape_para_error_TTbar);
                  params_list.append(self.workspace4limit_.var("Deco_TTbar_signal_region_%s_%s_mlvj_relaxed_eig0"%(self.channel, self.wtagger_label)));
                 else:     
                  self.workspace4limit_.var("Deco_TTbar_signal_region_%s_%s_mlvj_eig0"%(self.channel, self.wtagger_label)).setError(self.shape_para_error_TTbar);
                  params_list.append(self.workspace4limit_.var("Deco_TTbar_signal_region_%s_%s_mlvj_eig0"%(self.channel, self.wtagger_label)));

            if self.MODEL_4_mlvj=="ExpN" or self.MODEL_4_mlvj=="ExpTail" or self.MODEL_4_mlvj=="Pow2" :

                self.workspace4limit_.var("Deco_WJets0_sb_lo_from_fitting_%s_%s_mlvj_eig0"%(self.channel, self.wtagger_label)).setError(self.shape_para_error_WJets0);
                self.workspace4limit_.var("Deco_WJets0_sb_lo_from_fitting_%s_%s_mlvj_eig1"%(self.channel, self.wtagger_label)).setError(self.shape_para_error_WJets0);
                self.workspace4limit_.var("Deco_WJets0_sb_lo_from_fitting_%s_%s_mlvj_eig2"%(self.channel, self.wtagger_label)).setError(self.shape_para_error_WJets0);

                params_list.append(self.workspace4limit_.var("Deco_WJets0_sb_lo_from_fitting_%s_%s_mlvj_eig0"%(self.channel, self.wtagger_label)));
                params_list.append(self.workspace4limit_.var("Deco_WJets0_sb_lo_from_fitting_%s_%s_mlvj_eig1"%(self.channel, self.wtagger_label)));
                params_list.append(self.workspace4limit_.var("Deco_WJets0_sb_lo_from_fitting_%s_%s_mlvj_eig2"%(self.channel, self.wtagger_label)));

                self.workspace4limit_.var("Deco_WJets0_sim_%s_%s_mlvj_eig0"%(self.channel, self.wtagger_label)).setError(self.shape_para_error_alpha);
                self.workspace4limit_.var("Deco_WJets0_sim_%s_%s_mlvj_eig1"%(self.channel, self.wtagger_label)).setError(self.shape_para_error_alpha);
                self.workspace4limit_.var("Deco_WJets0_sim_%s_%s_mlvj_eig2"%(self.channel, self.wtagger_label)).setError(self.shape_para_error_alpha);
                self.workspace4limit_.var("Deco_WJets0_sim_%s_%s_mlvj_eig3"%(self.channel, self.wtagger_label)).setError(self.shape_para_error_alpha);

                params_list.append(self.workspace4limit_.var("Deco_WJets0_sim_%s_%s_mlvj_eig0"%(self.channel, self.wtagger_label)))
                params_list.append(self.workspace4limit_.var("Deco_WJets0_sim_%s_%s_mlvj_eig1"%(self.channel, self.wtagger_label)))
                params_list.append(self.workspace4limit_.var("Deco_WJets0_sim_%s_%s_mlvj_eig2"%(self.channel, self.wtagger_label)))
                params_list.append(self.workspace4limit_.var("Deco_WJets0_sim_%s_%s_mlvj_eig3"%(self.channel, self.wtagger_label)))


                ### TTbar use exp
                if isTTbarFloating !=0:
                    if useRelaxedShape == 1 :
                     self.workspace4limit_.var("Deco_TTbar_signal_region_%s_%s_mlvj_relaxed_eig0"%(self.channel, self.wtagger_label)).setError(self.shape_para_error_TTbar);
                     params_list.append(self.workspace4limit_.var("Deco_TTbar_signal_region_%s_%s_mlvj_relaxed_eig0"%(self.channel, self.wtagger_label)));
                    else:    
                     self.workspace4limit_.var("Deco_TTbar_signal_region_%s_%s_mlvj_eig0"%(self.channel, self.wtagger_label)).setError(self.shape_para_error_TTbar);
                     params_list.append(self.workspace4limit_.var("Deco_TTbar_signal_region_%s_%s_mlvj_eig0"%(self.channel, self.wtagger_label)));

        ### print the datacard                                       
        self.print_limit_datacard("unbin", "ggH", params_list);
        self.print_limit_datacard("unbin", "vbfH", params_list);
        self.print_limit_datacard("unbin", "ggHvbfH", params_list);

        if mode=="sideband_correction_method1":

          if self.MODEL_4_mlvj=="ErfExp_v1" or self.MODEL_4_mlvj=="ErfPow_v1" or self.MODEL_4_mlvj=="2Exp" :

                self.FloatingParams.add(self.workspace4limit_.var("Deco_WJets0_sb_lo_from_fitting_%s_%s_mlvj_eig0"%(self.channel, self.wtagger_label)) );
                self.FloatingParams.add(self.workspace4limit_.var("Deco_WJets0_sb_lo_from_fitting_%s_%s_mlvj_eig1"%(self.channel, self.wtagger_label)) );
                self.FloatingParams.add(self.workspace4limit_.var("Deco_WJets0_sb_lo_from_fitting_%s_%s_mlvj_eig2"%(self.channel, self.wtagger_label)) );
                self.FloatingParams.add(self.workspace4limit_.var("Deco_WJets0_sb_lo_from_fitting_%s_%s_mlvj_eig3"%(self.channel, self.wtagger_label)) );

                self.FloatingParams.add(self.workspace4limit_.var("Deco_WJets0_sim_%s_%s_mlvj_eig0"%(self.channel, self.wtagger_label)) );
                self.FloatingParams.add(self.workspace4limit_.var("Deco_WJets0_sim_%s_%s_mlvj_eig1"%(self.channel, self.wtagger_label)) );
                self.FloatingParams.add(self.workspace4limit_.var("Deco_WJets0_sim_%s_%s_mlvj_eig2"%(self.channel, self.wtagger_label)) );
                self.FloatingParams.add(self.workspace4limit_.var("Deco_WJets0_sim_%s_%s_mlvj_eig3"%(self.channel, self.wtagger_label)) );
                self.FloatingParams.add(self.workspace4limit_.var("Deco_WJets0_sim_%s_%s_mlvj_eig4"%(self.channel, self.wtagger_label)) );
                self.FloatingParams.add(self.workspace4limit_.var("Deco_WJets0_sim_%s_%s_mlvj_eig5"%(self.channel, self.wtagger_label)) );

                if isTTbarFloating!=0:
                  if useRelaxedShape == 1:
                   self.FloatingParams.add(self.workspace4limit_.var("Deco_TTbar_signal_region_%s_%s_mlvj_relaxed_eig0"%(self.channel, self.wtagger_label)) );
                   self.FloatingParams.add(self.workspace4limit_.var("Deco_TTbar_signal_region_%s_%s_mlvj_relaxed_eig1"%(self.channel, self.wtagger_label)) );
                   self.FloatingParams.add(self.workspace4limit_.var("Deco_TTbar_signal_region_%s_%s_mlvj_relaxed_eig2"%(self.channel, self.wtagger_label)) );
                  else:    
                   self.FloatingParams.add(self.workspace4limit_.var("Deco_TTbar_signal_region_%s_%s_mlvj_eig0"%(self.channel, self.wtagger_label)) );
                   self.FloatingParams.add(self.workspace4limit_.var("Deco_TTbar_signal_region_%s_%s_mlvj_eig1"%(self.channel, self.wtagger_label)) );
                   self.FloatingParams.add(self.workspace4limit_.var("Deco_TTbar_signal_region_%s_%s_mlvj_eig2"%(self.channel, self.wtagger_label)) );

          if self.MODEL_4_mlvj=="ErfPow2_v1" or self.MODEL_4_mlvj=="ErfPowExp_v1" :

                self.FloatingParams.add(self.workspace4limit_.var("Deco_WJets0_sb_lo_from_fitting_%s_%s_mlvj_eig0"%(self.channel, self.wtagger_label)) );
                self.FloatingParams.add(self.workspace4limit_.var("Deco_WJets0_sb_lo_from_fitting_%s_%s_mlvj_eig1"%(self.channel, self.wtagger_label)) );
                self.FloatingParams.add(self.workspace4limit_.var("Deco_WJets0_sb_lo_from_fitting_%s_%s_mlvj_eig2"%(self.channel, self.wtagger_label)) );
                self.FloatingParams.add(self.workspace4limit_.var("Deco_WJets0_sb_lo_from_fitting_%s_%s_mlvj_eig3"%(self.channel, self.wtagger_label)) );
                self.FloatingParams.add(self.workspace4limit_.var("Deco_WJets0_sb_lo_from_fitting_%s_%s_mlvj_eig4"%(self.channel, self.wtagger_label)) );

                self.FloatingParams.add(self.workspace4limit_.var("Deco_WJets0_sim_%s_%s_mlvj_eig0"%(self.channel, self.wtagger_label)) );
                self.FloatingParams.add(self.workspace4limit_.var("Deco_WJets0_sim_%s_%s_mlvj_eig1"%(self.channel, self.wtagger_label)) );
                self.FloatingParams.add(self.workspace4limit_.var("Deco_WJets0_sim_%s_%s_mlvj_eig2"%(self.channel, self.wtagger_label)) );
                self.FloatingParams.add(self.workspace4limit_.var("Deco_WJets0_sim_%s_%s_mlvj_eig3"%(self.channel, self.wtagger_label)) );
                self.FloatingParams.add(self.workspace4limit_.var("Deco_WJets0_sim_%s_%s_mlvj_eig4"%(self.channel, self.wtagger_label)) );
                self.FloatingParams.add(self.workspace4limit_.var("Deco_WJets0_sim_%s_%s_mlvj_eig5"%(self.channel, self.wtagger_label)) );
                self.FloatingParams.add(self.workspace4limit_.var("Deco_WJets0_sim_%s_%s_mlvj_eig6"%(self.channel, self.wtagger_label)) );
                self.FloatingParams.add(self.workspace4limit_.var("Deco_WJets0_sim_%s_%s_mlvj_eig7"%(self.channel, self.wtagger_label)) );

                if isTTbarFloating!=0:
                   if useRelaxedShape == 1:
                     self.FloatingParams.add(self.workspace4limit_.var("Deco_TTbar_signal_region_%s_%s_mlvj_relaxed_eig0"%(self.channel, self.wtagger_label)));
                     self.FloatingParams.add(self.workspace4limit_.var("Deco_TTbar_signal_region_%s_%s_mlvj_relaxed_eig1"%(self.channel, self.wtagger_label)));
                     self.FloatingParams.add(self.workspace4limit_.var("Deco_TTbar_signal_region_%s_%s_mlvj_relaxed_eig2"%(self.channel, self.wtagger_label)));
                     self.FloatingParams.add(self.workspace4limit_.var("Deco_TTbar_signal_region_%s_%s_mlvj_relaxed_eig3"%(self.channel, self.wtagger_label)));
                   else:     
                     self.FloatingParams.add(self.workspace4limit_.var("Deco_TTbar_signal_region_%s_%s_mlvj_eig0"%(self.channel, self.wtagger_label)));
                     self.FloatingParams.add(self.workspace4limit_.var("Deco_TTbar_signal_region_%s_%s_mlvj_eig1"%(self.channel, self.wtagger_label)));
                     self.FloatingParams.add(self.workspace4limit_.var("Deco_TTbar_signal_region_%s_%s_mlvj_eig2"%(self.channel, self.wtagger_label)));
                     self.FloatingParams.add(self.workspace4limit_.var("Deco_TTbar_signal_region_%s_%s_mlvj_eig3"%(self.channel, self.wtagger_label)));

          if self.MODEL_4_mlvj=="Exp" or self.MODEL_4_mlvj=="Pow" :

                self.FloatingParams.add(self.workspace4limit_.var("Deco_WJets0_sb_lo_from_fitting_%s_%s_mlvj_eig0"%(self.channel, self.wtagger_label)) );
                self.FloatingParams.add(self.workspace4limit_.var("Deco_WJets0_sb_lo_from_fitting_%s_%s_mlvj_eig1"%(self.channel, self.wtagger_label)) );

                self.FloatingParams.add(self.workspace4limit_.var("Deco_WJets0_sim_%s_%s_mlvj_eig0"%(self.channel, self.wtagger_label)) );
                self.FloatingParams.add(self.workspace4limit_.var("Deco_WJets0_sim_%s_%s_mlvj_eig1"%(self.channel, self.wtagger_label)) );

                if isTTbarFloating!=0:
                 if useRelaxedShape == 1:
                  self.FloatingParams.add(self.workspace4limit_.var("Deco_TTbar_signal_region_%s_%s_mlvj_relaxed_eig0"%(self.channel,self.wtagger_label)));
                 else:    
                  self.FloatingParams.add(self.workspace4limit_.var("Deco_TTbar_signal_region_%s_%s_mlvj_eig0"%(self.channel,self.wtagger_label)));


          if self.MODEL_4_mlvj=="ExpN" or self.MODEL_4_mlvj=="ExpTail" or self.MODEL_4_mlvj=="Pow2" :

                self.FloatingParams.add(self.workspace4limit_.var("Deco_WJets0_sb_lo_from_fitting_%s_%s_mlvj_eig0"%(self.channel, self.wtagger_label)) );
                self.FloatingParams.add(self.workspace4limit_.var("Deco_WJets0_sb_lo_from_fitting_%s_%s_mlvj_eig1"%(self.channel, self.wtagger_label)) );
                self.FloatingParams.add(self.workspace4limit_.var("Deco_WJets0_sb_lo_from_fitting_%s_%s_mlvj_eig2"%(self.channel, self.wtagger_label)) );


                self.FloatingParams.add(self.workspace4limit_.var("Deco_WJets0_sim_%s_%s_mlvj_eig0"%(self.channel, self.wtagger_label)) );
                self.FloatingParams.add(self.workspace4limit_.var("Deco_WJets0_sim_%s_%s_mlvj_eig1"%(self.channel, self.wtagger_label)) );
                self.FloatingParams.add(self.workspace4limit_.var("Deco_WJets0_sim_%s_%s_mlvj_eig2"%(self.channel, self.wtagger_label)) );
                self.FloatingParams.add(self.workspace4limit_.var("Deco_WJets0_sim_%s_%s_mlvj_eig3"%(self.channel, self.wtagger_label)) );

                if isTTbarFloating!=0:
                   if useRelaxedShape == 1: 
                     self.FloatingParams.add(self.workspace4limit_.var("Deco_TTbar_signal_region_%s_%s_mlvj_relaxed_eig0"%(self.channel,self.wtagger_label)));
                   else:   
                     self.FloatingParams.add(self.workspace4limit_.var("Deco_TTbar_signal_region_%s_%s_mlvj_eig0"%(self.channel,self.wtagger_label)));


        ### Add the floating list to the combiner --> the pdf which are not fixed are floating by default
        getattr(self.workspace4limit_,"import")(self.FloatingParams);

        ### Save the workspace
        self.save_workspace_to_file();


    #### Method used in order to save the workspace in a output root file
    def save_workspace_to_file(self):
        self.workspace4limit_.writeToFile(self.file_rlt_root);
        self.file_out.close()


    #### Method used to print the general format of the datacard for both counting and unbinned analysis         
    def print_limit_datacard(self, mode, signalchannel, params_list=[] ): #mode:unbin or counting

      print "############## print_limit_datacard for %s %s ################"%(mode,signalchannel)

      if (mode == "unbin" or mode == "counting"): 
         print "print_limit_datacard use wrong mode: %s"%(mode);#raw_input("ENTER");

         ### open the datacard
         datacard_out = open(getattr(self,"file_datacard_%s_%s"%(mode, signalchannel)),"w");
         datacard_out.write( "imax 1" )
         if signalchannel == "ggH" or signalchannel == "vbfH":
            datacard_out.write( "\njmax *" )
         elif signalchannel=="ggHvbfH":
            datacard_out.write( "\njmax *" )
         else:
            raw_input("Wrong signal channel, please check!!");
            
         datacard_out.write( "\nkmax *" )
         datacard_out.write( "\n--------------- ")


         datacard_out.write( "\nbin CMS_%s"%(self.channel));
         if mode == "unbin":
            datacard_out.write("\nobservation %0.2f "%(self.workspace4limit_.data("data_obs_%s"%(self.channel)).sumEntries()));
         if mode == "counting":
            datacard_out.write("\nobservation %0.2f "%(self.workspace4limit_.var("observation_for_counting").getVal()));

         datacard_out.write( "\n------------------------------" );

         if mode == "unbin":
          fnOnly = ntpath.basename(self.file_rlt_root)
          getattr(self.workspace4limit_,"import")(self.workspace4fit_.pdf("model_pdf_%s_signal_region_%s_mlvj"%(self.higgs_sample,self.channel)).clone(self.higgs_sample+"_%s"%(self.channel)))
          getattr(self.workspace4limit_,"import")(self.workspace4fit_.pdf("model_pdf_%s_signal_region_%s_mlvj"%(self.vbfhiggs_sample,self.channel)).clone(self.vbfhiggs_sample+"_%s"%(self.channel)))

          if signalchannel == "ggH":
              datacard_out.write("\nshapes %s CMS_%s %s %s:$PROCESS_%s"%(self.higgs_sample,self.channel,fnOnly,self.workspace4limit_.GetName(),self.channel));
          elif signalchannel == "vbfH":
              datacard_out.write("\nshapes %s CMS_%s %s %s:$PROCESS_%s"%(self.vbfhiggs_sample,self.channel,fnOnly,self.workspace4limit_.GetName(),self.channel));
          elif signalchannel == "ggHvbfH":
              datacard_out.write("\nshapes %s CMS_%s %s %s:$PROCESS_%s"%(self.higgs_sample,self.channel,fnOnly,self.workspace4limit_.GetName(),self.channel));
              datacard_out.write("\nshapes %s CMS_%s %s %s:$PROCESS_%s"%(self.vbfhiggs_sample,self.channel,fnOnly,self.workspace4limit_.GetName(),self.channel));
          
          datacard_out.write("\nshapes WJets CMS_%s %s %s:$PROCESS_%s"%(self.channel,fnOnly,self.workspace4limit_.GetName(),self.channel));
          datacard_out.write("\nshapes TTbar CMS_%s %s %s:$PROCESS_%s"%(self.channel,fnOnly,self.workspace4limit_.GetName(),self.channel));
          datacard_out.write("\nshapes STop CMS_%s %s %s:$PROCESS_%s"%(self.channel,fnOnly,self.workspace4limit_.GetName(),self.channel));
          datacard_out.write("\nshapes VV CMS_%s %s %s:$PROCESS_%s"%(self.channel,fnOnly,self.workspace4limit_.GetName(),self.channel));
          datacard_out.write("\nshapes WW_EWK CMS_%s %s %s:$PROCESS_%s"%(self.channel,fnOnly,self.workspace4limit_.GetName(),self.channel));
          datacard_out.write("\nshapes data_obs CMS_%s %s %s:$PROCESS_%s"%(self.channel,fnOnly,self.workspace4limit_.GetName(), 
self.channel));
          datacard_out.write( "\n--------------- ")
          

         if signalchannel == "ggH":
            datacard_out.write( "\nbin                CMS_%s    CMS_%s   CMS_%s   CMS_%s  CMS_%s   CMS_%s"%(self.channel,self.channel,self.channel,self.channel,self.channel,self.channel));
            datacard_out.write( "\nprocess            %s        WJets    TTbar    STop    VV     WW_EWK"%(self.higgs_sample))
            datacard_out.write( "\nprocess            -1                 1        2        3       4     5" )

            if mode == "unbin":
                datacard_out.write( "\nrate          %0.2f          %0.2f   %0.2f    %0.2f    %0.2f     %0.2f "%(self.workspace4limit_.var("rate_%s_for_unbin"%(self.higgs_sample)).getVal(),self.workspace4limit_.var("rate_WJets_for_unbin").getVal(), self.workspace4limit_.var("rate_TTbar_for_unbin").getVal(), self.workspace4limit_.var("rate_STop_for_unbin").getVal(), self.workspace4limit_.var("rate_VV_for_unbin").getVal(), self.workspace4limit_.var("rate_WW_EWK_for_unbin").getVal()));

            elif mode == "counting":
                datacard_out.write( "\nrate          %0.2f          %0.2f   %0.2f    %0.2f    %0.2f    %0.2f "%(self.workspace4limit_.var("rate_%s_for_counting"%(self.higgs_sample)).getVal(), self.workspace4limit_.var("rate_WJets_for_counting").getVal(), self.workspace4limit_.var("rate_TTbar_for_counting").getVal(), self.workspace4limit_.var("rate_STop_for_counting").getVal(), self.workspace4limit_.var("rate_VV_for_counting").getVal(), self.workspace4limit_.var("rate_WW_EWK_for_counting").getVal()));
                
            datacard_out.write( "\n-------------------------------- " )

            datacard_out.write( "\nQCDscale_ggH lnN   %0.3f     -             -        -       -       -     -"%(1.+self.QCDscale_ggH))

            datacard_out.write( "\nQCDscale_ggH1in lnN   %0.3f     -             -        -       -       -     -"%(1.+self.QCDscale_ggH1in))

            datacard_out.write( "\nQCDscale_ggH2in lnN   %0.3f     -             -        -       -       -     -"%(1.+self.QCDscale_ggH2in))   

            datacard_out.write( "\npdf_gg       lnN   %0.3f     -             -        -       -       -     -"%(1.+self.pdf_gg))

            datacard_out.write( "\nQCDscale_ggH_ACCEPT lnN %0.3f   -             -        -       -       -     -"%(1.+self.hwwlnJ_pdfAcc_gg) )

            datacard_out.write( "\nintf_ggH  lnN      %0.3f     -             -        -       -       -     -"%(1.+self.interference_ggH_uncertainty) )

            datacard_out.write( "\nCMS_hwwlvj_STop  lnN       -         -             -        -       %0.3f   -     -"%(1+self.XS_STop_uncertainty) )

            datacard_out.write( "\nCMS_hwwlvj_VV    lnN       -         -             -        -       -       %0.3f    -"%(1+self.XS_VV_uncertainty) )

            datacard_out.write( "\nCMS_hwwlvj_WW_EWK    lnN       -         -             -        -       -       -     %0.3f"%(1+self.XS_WW_EWK_uncertainty))

            datacard_out.write( "\nCMS_hwwlvj_TTbar    lnN       -         -             -        %0.3f       -       -     -"%(1+self.XS_TTbar_uncertainty) )

 
         elif signalchannel=="vbfH":
            datacard_out.write( "\nbin                CMS_%s    CMS_%s   CMS_%s   CMS_%s  CMS_%s   CMS_%s"%(self.channel,self.channel,self.channel,self.channel,self.channel,self.channel));
            datacard_out.write( "\nprocess            %s        WJets    TTbar    STop    VV     WW_EWK"%(self.vbfhiggs_sample));
            datacard_out.write( "\nprocess            -1            1        2     3       4     5" );

            if mode == "unbin":
                datacard_out.write( "\nrate            %0.2f         %0.2f   %0.2f    %0.2f    %0.2f    %0.2f"%(self.workspace4limit_.var("rate_%s_for_unbin"%(self.vbfhiggs_sample)).getVal(), self.workspace4limit_.var("rate_WJets_for_unbin").getVal(), self.workspace4limit_.var("rate_TTbar_for_unbin").getVal(), self.workspace4limit_.var("rate_STop_for_unbin").getVal(), self.workspace4limit_.var("rate_VV_for_unbin").getVal(), self.workspace4limit_.var("rate_WW_EWK_for_unbin").getVal()  ) )

            elif mode == "counting":
                datacard_out.write( "\nrate            %0.2f         %0.2f   %0.2f    %0.2f    %0.2f    %0.2f"%(self.workspace4limit_.var("rate_%s_for_counting"%(self.vbfhiggs_sample)).getVal(), self.workspace4limit_.var("rate_WJets_for_counting").getVal(), self.workspace4limit_.var("rate_TTbar_for_counting").getVal(), self.workspace4limit_.var("rate_STop_for_counting").getVal(), self.workspace4limit_.var("rate_VV_for_counting").getVal(), self.workspace4limit_.var("rate_WW_EWK_for_counting").getVal()  ) )

            datacard_out.write( "\n-------------------------------- " )
            
            datacard_out.write( "\nQCDscale_vbfH lnN  -         %0.3f         -        -       -       -     -"%(1.+self.QCDscale_vbfH) )

            datacard_out.write( "\npdf_qqbar     lnN  -         %0.3f         -        -       -       -     -"%(1.+self.pdf_vbf))

            datacard_out.write( "\nQCDscale_qqH_ACCEPT lnN -      %0.3f         -        -       -       -     -"%(1.+self.hwwlnJ_pdfAcc_vbf))

            datacard_out.write( "\nintf_vbfH lnN      -         %0.3f         -        -       -       -     -"%(1.+self.interference_vbfH_uncertainty) )

            datacard_out.write( "\nCMS_hwwlvj_STop  lnN       -         -             -        -       %0.3f   -     -"%(1+self.XS_STop_uncertainty) )

            datacard_out.write( "\nCMS_hwwlvj_VV    lnN       -         -             -        -       -       %0.3f    -"%(1+self.XS_VV_uncertainty) )

            datacard_out.write( "\nCMS_hwwlvj_WW_EWK    lnN       -         -             -        -       -       -     %0.3f"%(1+self.XS_WW_EWK_uncertainty))

            datacard_out.write( "\nCMS_hwwlvj_TTbar    lnN       -         -             -        %0.3f       -       -     -"%(1+self.XS_TTbar_uncertainty) )

 
         elif signalchannel=="ggHvbfH":

            datacard_out.write( "\nbin                CMS_%s    CMS_%s    CMS_%s   CMS_%s   CMS_%s  CMS_%s   CMS_%s"%(self.channel,self.channel,self.channel,self.channel,self.channel,self.channel,self.channel));            
            datacard_out.write( "\nprocess            %s    %s       WJets    TTbar    STop    VV    WW_EWK"%(self.higgs_sample,self.vbfhiggs_sample) )
            datacard_out.write( "\nprocess            -1        0             1        2        3       4    5" )

            if mode == "unbin":
                datacard_out.write( "\nrate               %0.2f    %0.2f         %0.2f   %0.2f    %0.2f    %0.2f    %0.2f "%(self.workspace4limit_.var("rate_%s_for_unbin"%(self.higgs_sample)).getVal(),self.workspace4limit_.var("rate_%s_for_unbin"%(self.vbfhiggs_sample)).getVal(), self.workspace4limit_.var("rate_WJets_for_unbin").getVal(), self.workspace4limit_.var("rate_TTbar_for_unbin").getVal(), self.workspace4limit_.var("rate_STop_for_unbin").getVal(), self.workspace4limit_.var("rate_VV_for_unbin").getVal(), self.workspace4limit_.var("rate_WW_EWK_for_unbin").getVal()  ) )

            elif mode == "counting":
                datacard_out.write( "\nrate               %0.2f    %0.2f         %0.2f   %0.2f    %0.2f    %0.2f    %0.2f"%(self.workspace4limit_.var("rate_%s_for_counting"%(self.higgs_sample)).getVal(),self.workspace4limit_.var("rate_%s_for_counting"%(self.vbfhiggs_sample)).getVal(), self.workspace4limit_.var("rate_WJets_for_counting").getVal(), self.workspace4limit_.var("rate_TTbar_for_counting").getVal(), self.workspace4limit_.var("rate_STop_for_counting").getVal(), self.workspace4limit_.var("rate_VV_for_counting").getVal(), self.workspace4limit_.var("rate_WW_EWK_for_counting").getVal()  ) )


            datacard_out.write( "\n-------------------------------- " )

            datacard_out.write( "\nQCDscale_ggH lnN   %0.3f     -             -        -       -       -     -"%(1.+self.QCDscale_ggH))

            datacard_out.write( "\nQCDscale_ggH1in lnN   %0.3f     -             -        -       -       -     -"%(1.+self.QCDscale_ggH1in))

            datacard_out.write( "\nQCDscale_ggH2in lnN   %0.3f     -             -        -       -       -     -"%(1.+self.QCDscale_ggH2in))   

            datacard_out.write( "\npdf_gg       lnN   %0.3f     -             -        -       -       -     -"%(1.+self.pdf_gg))

            datacard_out.write( "\nQCDscale_ggH_ACCEPT lnN %0.3f   -             -        -       -       -     -"%(1.+self.hwwlnJ_pdfAcc_gg) )

            datacard_out.write( "\nintf_ggH  lnN      %0.3f     -             -        -       -       -     -"%(1.+self.interference_ggH_uncertainty) )
            
            datacard_out.write( "\nQCDscale_vbfH lnN  -         %0.3f         -        -       -       -     -"%(1.+self.QCDscale_vbfH) )

            datacard_out.write( "\npdf_qqbar     lnN  -         %0.3f         -        -       -       -     -"%(1.+self.pdf_vbf))

            datacard_out.write( "\nQCDscale_qqH_ACCEPT lnN -      %0.3f         -        -       -       -     -"%(1.+self.hwwlnJ_pdfAcc_vbf))

            datacard_out.write( "\nintf_vbfH lnN      -         %0.3f         -        -       -       -     -"%(1.+self.interference_vbfH_uncertainty) )

            datacard_out.write( "\nCMS_hwwlvj_STop  lnN       -         -             -        -       %0.3f   -     -"%(1+self.XS_STop_uncertainty) )

            datacard_out.write( "\nCMS_hwwlvj_VV    lnN       -         -             -        -       -       %0.3f    -"%(1+self.XS_VV_uncertainty) )

            datacard_out.write( "\nCMS_hwwlvj_WW_EWK    lnN       -         -             -        -       -       -     %0.3f"%(1+self.XS_WW_EWK_uncertainty))

            datacard_out.write( "\n#CMS_hwwlvj_TTbar    lnN       -         -             -        %0.3f       -       -     -"%(1+self.XS_TTbar_uncertainty) )

         datacard_out.write( "\nlumi_8TeV     lnN       %0.3f     %0.3f         -        %0.3f   %0.3f   %0.3f   %0.3f"%(1.+self.lumi_uncertainty,1.+self.lumi_uncertainty,1.+self.lumi_uncertainty,1.+self.lumi_uncertainty,1.+self.lumi_uncertainty,1.+self.lumi_uncertainty) )

         datacard_out.write( "\nCMS_trigger_%s lnN     %0.3f     %0.3f         -        %0.3f   %0.3f   %0.3f    %0.3f"%(self.channel,1+self.lep_trigger_uncertainty,1+self.lep_trigger_uncertainty,1+self.lep_trigger_uncertainty,1+self.lep_trigger_uncertainty,1+self.lep_trigger_uncertainty, 1+self.lep_trigger_uncertainty ) );

         datacard_out.write( "\nCMS_eff_%s lnN       %0.3f     %0.3f         -        %0.3f   %0.3f   %0.3f    %0.3f"%(self.channel, 1+self.lep_eff_uncertainty,1+self.lep_eff_uncertainty,1+self.lep_eff_uncertainty,1+self.lep_eff_uncertainty,1+self.lep_eff_uncertainty, 1+self.lep_eff_uncertainty ) );

         datacard_out.write( "\nCMS_Top_norm_%s_%d lnN    -         -             -        %0.3f   %0.3f   -      -"%(self.channel, options.jet_bin,1+self.rrv_wtagger_eff_reweight_forT.getError(), 1+self.rrv_wtagger_eff_reweight_forT.getError() ) );

         datacard_out.write( "\nCMS_wtagger lnN     %0.3f     %0.3f         -        -       -       %0.3f    %0.3f"%(1+self.rrv_wtagger_eff_reweight_forV.getError(), 1+self.rrv_wtagger_eff_reweight_forV.getError(), 1+self.rrv_wtagger_eff_reweight_forV.getError(), 1+self.rrv_wtagger_eff_reweight_forV.getError() ) );
            
         ### nousiance for the bkg
         ### WJets normaliztion due to data fit and alternate modellization
         if self.number_WJets_insideband >0:
            datacard_out.write( "\nWjet_Norm_%s_%d lnN %0.3f     -  %0.3f           -      -        -      -"%(self.channel,options.jet_bin,self.number_WJets_insideband, getattr(self,"datadriven_alpha_WJets_%s"%(mode))));
         else:
            datacard_out.write( "\nWjet_Norm_%s_%d lnN     -         -             %0.3f    -       -       -      -"%(self.channel,options.jet_bin, 1+ self.workspace4limit_.var("rate_WJets_for_unbin").getError()/self.workspace4limit_.var("rate_WJets_for_unbin").getVal() ) );


#         datacard_out.write( "\nCMS_btag_efficiency lnN     %0.3f     %0.3f         %0.3f        %0.3f   %0.3f   %0.3f    %0.3f"%(1+self.ggH_normalization_uncertainty_from_btag_scale, 1+self.vbf_normalization_uncertainty_from_btag_scale, 1+self.WJets_normalization_uncertainty_from_btag_scale, 1+self.TTbar_normalization_uncertainty_from_btag_scale, 1+self.STop_normalization_uncertainty_from_btag_scale, 1+self.VV_normalization_uncertainty_from_btag_scale, 1+self.WW_EWK_normalization_uncertainty_from_btag_scale ) );

#         datacard_out.write( "\nCMS_scale_%s lnN     %0.3f     %0.3f         %0.3f        %0.3f   %0.3f   %0.3f    %0.3f"%(self.channel,1+self.ggH_normalization_uncertainty_from_lep_scale, 1+self.vbf_normalization_uncertainty_from_lep_scale, 1+self.WJets_normalization_uncertainty_from_lep_scale, 1+self.TTbar_normalization_uncertainty_from_lep_scale, 1+self.STop_normalization_uncertainty_from_lep_scale, 1+self.VV_normalization_uncertainty_from_lep_scale, 1+self.WW_EWK_normalization_uncertainty_from_lep_scale ) );


         ## jet mass systematic scaling up and down vbf jets detajj, mjj, and pt selection effect
         if self.ggH_normalization_uncertainty_from_jet_scale!=0 and self.vbf_normalization_uncertainty_from_jet_scale!=0 and self.WJets_normalization_uncertainty_from_jet_scale!=0 and self.TTbar_normalization_uncertainty_from_jet_scale!=0 and self.STop_normalization_uncertainty_from_jet_scale!=0 and self.VV_normalization_uncertainty_from_jet_scale!=0 : 

          datacard_out.write( "\nCMS_scale_j lnN   %0.3f     %0.3f     %0.3f/%0.3f    %0.3f/%0.3f   %0.3f/%0.3f   %0.3f/%0.3f    %0.3f/%0.3f"%(1+self.ggH_normalization_uncertainty_from_jet_scale, 1+self.vbf_normalization_uncertainty_from_jet_scale, 1-self.WJets_normalization_uncertainty_from_jet_scale, 1+self.WJets_normalization_uncertainty_from_jet_scale, 1+self.TTbar_normalization_uncertainty_from_jet_scale, 1-self.TTbar_normalization_uncertainty_from_jet_scale, 1+self.STop_normalization_uncertainty_from_jet_scale, 1-self.STop_normalization_uncertainty_from_jet_scale, 1+self.VV_normalization_uncertainty_from_jet_scale, 1-self.VV_normalization_uncertainty_from_jet_scale, 1+self.WW_EWK_normalization_uncertainty_from_jet_scale, 1-self.WW_EWK_normalization_uncertainty_from_jet_scale ) )        

         if self.ggH_normalization_uncertainty_from_jet_res!=0 and self.vbf_normalization_uncertainty_from_jet_res!=0 and self.WJets_normalization_uncertainty_from_jet_res!=0 and self.TTbar_normalization_uncertainty_from_jet_res!=0 and self.STop_normalization_uncertainty_from_jet_res!=0 and self.VV_normalization_uncertainty_from_jet_res!=0 :
             
          datacard_out.write( "\nCMS_res_j lnN   %0.3f     %0.3f     %0.3f/%0.3f    %0.3f/%0.3f   %0.3f/%0.3f   %0.3f/%0.3f    %0.3f/%0.3f"%(1+self.ggH_normalization_uncertainty_from_jet_res, 1+self.vbf_normalization_uncertainty_from_jet_res, 1-self.WJets_normalization_uncertainty_from_jet_res, 1+self.WJets_normalization_uncertainty_from_jet_res, 1+self.TTbar_normalization_uncertainty_from_jet_res, 1-self.TTbar_normalization_uncertainty_from_jet_res, 1+self.STop_normalization_uncertainty_from_jet_res, 1-self.STop_normalization_uncertainty_from_jet_res, 1+self.VV_normalization_uncertainty_from_jet_res, 1-self.VV_normalization_uncertainty_from_jet_res, 1+self.WW_EWK_normalization_uncertainty_from_jet_res, 1-self.WW_EWK_normalization_uncertainty_from_jet_res ) )        


#         datacard_out.write( "\nCMS_res_l lnN   %0.3f     %0.3f     %0.3f    %0.3f   %0.3f   %0.3f    %0.3f"%(1+self.ggH_normalization_uncertainty_from_lep_res, 1+self.vbf_normalization_uncertainty_from_lep_res, 1+self.WJets_normalization_uncertainty_from_lep_res, 1+self.TTbar_normalization_uncertainty_from_lep_res, 1+self.STop_normalization_uncertainty_from_lep_res, 1+self.VV_normalization_uncertainty_from_lep_res, 1+self.WW_EWK_normalization_uncertainty_from_lep_res ) )

         if self.ggH_normalization_uncertainty_from_lep_scale!=0 and self.vbf_normalization_uncertainty_from_lep_scale!=0 and self.WJets_normalization_uncertainty_from_lep_scale!=0 and self.TTbar_normalization_uncertainty_from_lep_scale!=0 and self.STop_normalization_uncertainty_from_lep_scale!=0 and self.VV_normalization_uncertainty_from_lep_scale!=0 : 

          datacard_out.write( "\nCMS_scale_l lnN   %0.3f     %0.3f     %0.3f    %0.3f   %0.3f   %0.3f    %0.3f"%(self.ggH_normalization_uncertainty_from_lep_scale, self.vbf_normalization_uncertainty_from_lep_scale, self.WJets_normalization_uncertainty_from_lep_scale, self.TTbar_normalization_uncertainty_from_lep_scale, self.STop_normalization_uncertainty_from_lep_scale, self.VV_normalization_uncertainty_from_lep_scale, self.WW_EWK_normalization_uncertainty_from_lep_scale ) )        


         if self.ggH_normalization_uncertainty_from_lep_res!=0 and self.vbf_normalization_uncertainty_from_lep_res!=0 and self.WJets_normalization_uncertainty_from_lep_res!=0 and self.TTbar_normalization_uncertainty_from_lep_res!=0 and self.STop_normalization_uncertainty_from_lep_res!=0 and self.VV_normalization_uncertainty_from_lep_res!=0 : 

          datacard_out.write( "\nCMS_res_l lnN   %0.3f     %0.3f     %0.3f    %0.3f   %0.3f   %0.3f    %0.3f"%(self.ggH_normalization_uncertainty_from_lep_res, self.vbf_normalization_uncertainty_from_lep_res, self.WJets_normalization_uncertainty_from_lep_res, self.TTbar_normalization_uncertainty_from_lep_res, self.STop_normalization_uncertainty_from_lep_res, self.VV_normalization_uncertainty_from_lep_res, self.WW_EWK_normalization_uncertainty_from_lep_res ) )


         if self.ggH_normalization_uncertainty_from_btag!=0 and self.vbf_normalization_uncertainty_from_btag!=0 and self.WJets_normalization_uncertainty_from_btag!=0 and self.TTbar_normalization_uncertainty_from_btag!=0 and self.STop_normalization_uncertainty_from_btag!=0 and self.VV_normalization_uncertainty_from_btag!=0 : 

          datacard_out.write( "\nCMS_btag_eff lnN   %0.3f     %0.3f     %0.3f    %0.3f   %0.3f   %0.3f    %0.3f"%(self.ggH_normalization_uncertainty_from_btag, self.vbf_normalization_uncertainty_from_btag, self.WJets_normalization_uncertainty_from_btag, self.TTbar_normalization_uncertainty_from_btag, self.STop_normalization_uncertainty_from_btag, self.VV_normalization_uncertainty_from_btag, self.WW_EWK_normalization_uncertainty_from_btag ) )                  



         if mode == "unbin":
            for i in range(len(params_list)):
                if TString(params_list[i].GetName()).Contains("Deco_TTbar_signal_region"):
                    datacard_out.write( "\n%s param  %0.1f  %0.1f "%( params_list[i].GetName(), params_list[i].getVal(), params_list[i].getError() ) ) 
                else:
                    datacard_out.write( "\n%s param  %0.1f  %0.1f "%( params_list[i].GetName(), params_list[i].getVal(), params_list[i].getError() ) ) 
         if mode == "counting":
            datacard_out.write( "\nShape    lnN       -         -             %0.3f    -       -       -      -"%(1+self.rrv_counting_uncertainty_from_shape_uncertainty.getError()))


    ### in order to get the pull
    def read_workspace(self):

        ### Taket the workspace for limits
        file = TFile(self.file_rlt_root) ;
        workspace = file.Get("workspace4limit_") ;
        workspace.Print()

        parameters_workspace = workspace.allVars();
        par = parameters_workspace.createIterator();
        par.Reset();
        param = par.Next()
        while (param):
            param.Print();
            param = par.Next()
        print "___________________________________________________"

        workspace.data("data_obs_%s"%(self.channel)).Print()
        print "_________________ Pdf in the Workspace  __________________________________"
        pdfs_workspace = workspace.allPdfs();
        par = pdfs_workspace.createIterator();
        par.Reset();
        param = par.Next()
        while (param):
            param.Print();
            param = par.Next()
        print "___________________________________________________"


        rrv_x = workspace.var("rrv_mass_lvj")
        data_obs = workspace.data("data_obs_%s"%(self.channel))
        model_pdf_ggH   = workspace.pdf("%s_%s"%(self.higgs_sample,self.channel))
        model_pdf_vbfH  = workspace.pdf("%s_%s"%(self.vbfhiggs_sample,self.channel))
        model_pdf_WJets = workspace.pdf("WJets_%s"%(self.channel))
        model_pdf_VV = workspace.pdf("VV_%s"%(self.channel))
        model_pdf_WW_EWK = workspace.pdf("WW_EWK_%s"%(self.channel))
        model_pdf_TTbar = workspace.pdf("TTbar_%s"%(self.channel))
        model_pdf_STop  = workspace.pdf("STop_%s"%(self.channel))

        model_pdf_ggH.Print();
        model_pdf_vbfH.Print();
        model_pdf_WJets.Print();
        model_pdf_VV.Print();
        model_pdf_TTbar.Print();
        model_pdf_STop.Print();
        model_pdf_WW_EWK.Print();

        rrv_number_ggH = workspace.var("rate_%s_for_unbin"%(self.higgs_sample))
        rrv_number_vbfH = workspace.var("rate_%s_for_unbin"%(self.vbfhiggs_sample))
        rrv_number_WJets = workspace.var("rate_WJets_for_unbin")
        rrv_number_VV = workspace.var("rate_VV_for_unbin")
        rrv_number_WW_EWK = workspace.var("rate_WW_EWK_for_unbin")        
        rrv_number_TTbar = workspace.var("rate_TTbar_for_unbin")
        rrv_number_STop = workspace.var("rate_STop_for_unbin")

        rrv_number_ggH.Print();
        rrv_number_vbfH.Print();
        rrv_number_WJets.Print();
        rrv_number_VV.Print();
        rrv_number_WW_EWK.Print();       
        rrv_number_TTbar.Print();
        rrv_number_STop.Print();

        rrv_number_Total_background_MC = RooRealVar("rrv_number_Total_background_MC","rrv_number_Total_background_MC",
                rrv_number_WJets.getVal()+
                rrv_number_VV.getVal()+
                rrv_number_WW_EWK.getVal()+                                                    
                rrv_number_TTbar.getVal()+
                rrv_number_STop.getVal());
        rrv_number_Total_background_MC.setError(TMath.Sqrt(
                rrv_number_WJets.getError()* rrv_number_WJets.getError()+
                rrv_number_VV.getError()* rrv_number_VV.getError()+
                rrv_number_WW_EWK.getError()* rrv_number_WW_EWK.getError()+                
                rrv_number_TTbar.getError()* rrv_number_TTbar.getError()+
                rrv_number_STop.getError() *rrv_number_STop.getError() 
                ));


        model_Total_background_MC = RooAddPdf("model_Total_background_MC","model_Total_background_MC",RooArgList(model_pdf_WJets,model_pdf_VV,model_pdf_WW_EWK,model_pdf_TTbar,model_pdf_STop),RooArgList(rrv_number_WJets,rrv_number_VV,rrv_number_WW_EWK,rrv_number_TTbar,rrv_number_STop));


        scale_number_ggH  = rrv_number_ggH.getVal()/data_obs.sumEntries();
        scale_number_vbfH = rrv_number_vbfH.getVal()/data_obs.sumEntries();
        scale_number_Total_background_MC = rrv_number_Total_background_MC.getVal()/data_obs.sumEntries();


                
        mplot = rrv_x.frame(RooFit.Title("check_workspace"));
        data_obs.plotOn(mplot ,RooFit.DataError(RooAbsData.SumW2), RooFit.Name("data_invisible"),RooFit.Invisible());


        #### create the frame
        model_Total_background_MC.plotOn(mplot,RooFit.Normalization(scale_number_Total_background_MC),RooFit.Name("WJets"), RooFit.Components("WJets_%s,WW_EWK_%s,VV_%s,TTbar_%s,STop_%s"%(self.channel,self.channel,self.channel,self.channel,self.channel)),RooFit.DrawOption("F"), RooFit.FillColor(self.color_palet["WJets"]), RooFit.LineColor(self.color_palet["WJets"]), RooFit.VLines());

        model_Total_background_MC.plotOn(mplot,RooFit.Normalization(scale_number_Total_background_MC),RooFit.Name("WW_EWK"), RooFit.Components("WW_EWK_%s,VV_%s,TTbar_%s,STop_%s"%(self.channel,self.channel,self.channel,self.channel)),RooFit.DrawOption("F"), RooFit.FillColor(self.color_palet["WW_EWK"]), RooFit.LineColor(self.color_palet["WW_EWK"]), RooFit.VLines());        

        model_Total_background_MC.plotOn(mplot,RooFit.Normalization(scale_number_Total_background_MC),RooFit.Name("VV"), RooFit.Components("VV_%s,TTbar_%s,STop_%s"%(self.channel,self.channel,self.channel)),RooFit.DrawOption("F"), RooFit.FillColor(self.color_palet["VV"]), RooFit.LineColor(self.color_palet["VV"]), RooFit.VLines());

        model_Total_background_MC.plotOn(mplot,RooFit.Normalization(scale_number_Total_background_MC),RooFit.Name("TTbar"), RooFit.Components("TTbar_%s,STop_%s"%(self.channel,self.channel)),RooFit.DrawOption("F"), RooFit.FillColor(self.color_palet["TTbar"]), RooFit.LineColor(self.color_palet["TTbar"]), RooFit.VLines());

        model_Total_background_MC.plotOn(mplot,RooFit.Normalization(scale_number_Total_background_MC),RooFit.Name("STop"), RooFit.Components("STop_%s"%(self.channel)),RooFit.DrawOption("F"), RooFit.FillColor(self.color_palet["STop"]), RooFit.LineColor(self.color_palet["STop"]), RooFit.VLines());                


        #solid line
        model_Total_background_MC.plotOn(mplot,RooFit.Normalization(scale_number_Total_background_MC),RooFit.Name("WJets_line_invisible"), RooFit.Components("WJets_xww_%s_%s,WW_EWK_xww_%s_%s,VV_xww_%s_%s,TTbar_xww_%s_%s,STop_xww_%s_%s"%(self.channel,self.wtagger_label,self.channel,self.wtagger_label,self.channel,self.wtagger_label,self.channel,self.wtagger_label,self.channel,self.wtagger_label)), RooFit.LineColor(kBlack), RooFit.LineWidth(2), RooFit.VLines());

        model_Total_background_MC.plotOn(mplot,RooFit.Normalization(scale_number_Total_background_MC),RooFit.Name("WW_EWK_line_invisible"), RooFit.Components("WW_EWK_xww_%s_%s,VV_xww_%s_%s,TTbar_xww_%s_%s,STop_xww_%s_%s"%(self.channel,self.wtagger_label,self.channel,self.wtagger_label,self.channel,self.wtagger_label,self.channel,self.wtagger_label)), RooFit.LineColor(kBlack), RooFit.LineWidth(2), RooFit.VLines());

        model_Total_background_MC.plotOn(mplot,RooFit.Normalization(scale_number_Total_background_MC),RooFit.Name("VV_line_invisible"), RooFit.Components("VV_xww_%s_%s,TTbar_xww_%s_%s,STop_xww_%s_%s"%(self.channel,self.wtagger_label,self.channel,self.wtagger_label,self.channel,self.wtagger_label)), RooFit.LineColor(kBlack), RooFit.LineWidth(2), RooFit.VLines());

        model_Total_background_MC.plotOn(mplot,RooFit.Normalization(scale_number_Total_background_MC),RooFit.Name("TTbar_line_invisible"), RooFit.Components("TTbar_xww_%s_%s,STop_xww_%s_%s"%(self.channel,self.wtagger_label,self.channel,self.wtagger_label)), RooFit.LineColor(kBlack), RooFit.LineWidth(2), RooFit.VLines());

        model_Total_background_MC.plotOn(mplot,RooFit.Normalization(scale_number_Total_background_MC),RooFit.Name("STop_line_invisible"), RooFit.Components("STop_xww_%s_%s"%(self.channel,self.wtagger_label)), RooFit.LineColor(kBlack), RooFit.LineWidth(2), RooFit.VLines());


        if self.higgs_sample=="ggH600" or self.higgs_sample=="ggH700":
           signal_scale = 2;
        else: 
           signal_scale = 2;
        
        if self.higgs_sample=="ggH600":
            model_pdf_ggH.plotOn(mplot,RooFit.Normalization(scale_number_ggH*signal_scale),RooFit.Name("ggH#times%s, m_{H}=0.6TeV"%(signal_scale)),RooFit.DrawOption("L"), RooFit.LineColor(self.color_palet["ggH"]), RooFit.LineStyle(2), RooFit.VLines());
            model_pdf_vbfH.plotOn(mplot,RooFit.Normalization(scale_number_vbfH*signal_scale),RooFit.Name("qqH#times%s, m_{H}=0.6TeV"%(signal_scale)),RooFit.DrawOption("L"), RooFit.LineColor(self.color_palet["vbfH"]), RooFit.LineStyle( 9), RooFit.VLines());

        if self.higgs_sample=="ggH700":
            model_pdf_ggH.plotOn(mplot,RooFit.Normalization(scale_number_ggH*signal_scale),RooFit.Name("ggH#times%s, m_{H}=0.7TeV"%(signal_scale)),RooFit.DrawOption("L"), RooFit.LineColor(self.color_palet["ggH"]), RooFit.LineStyle(2), RooFit.VLines());
            model_pdf_vbfH.plotOn(mplot,RooFit.Normalization(scale_number_vbfH*signal_scale),RooFit.Name("qqH#times%s, m_{H}=0.7TeV"%(signal_scale)),RooFit.DrawOption("L"), RooFit.LineColor(self.color_palet["vbfH"]), RooFit.LineStyle( 9), RooFit.VLines());

        if self.higgs_sample=="ggH800":
            model_pdf_ggH.plotOn(mplot,RooFit.Normalization(scale_number_ggH*signal_scale),RooFit.Name("ggH#times%s, m_{H}=0.8TeV"%(signal_scale)),RooFit.DrawOption("L"), RooFit.LineColor(self.color_palet["ggH"]), RooFit.LineStyle(2), RooFit.VLines());
            model_pdf_vbfH.plotOn(mplot,RooFit.Normalization(scale_number_vbfH*signal_scale),RooFit.Name("qqH#times%s, m_{H}=0.8TeV"%(signal_scale)),RooFit.DrawOption("L"), RooFit.LineColor(self.color_palet["vbfH"]), RooFit.LineStyle( 9), RooFit.VLines());

        if self.higgs_sample=="ggH900":
            model_pdf_ggH.plotOn(mplot,RooFit.Normalization(scale_number_ggH*signal_scale),RooFit.Name("ggH#times%s, m_{H}=0.9TeV"%(signal_scale)),RooFit.DrawOption("L"), RooFit.LineColor(self.color_palet["ggH"]), RooFit.LineStyle(2), RooFit.VLines());
            model_pdf_vbfH.plotOn(mplot,RooFit.Normalization(scale_number_vbfH*signal_scale),RooFit.Name("qqH#times%s, m_{H}=0.9TeV"%(signal_scale)),RooFit.DrawOption("L"), RooFit.LineColor(self.color_palet["vbfH"]), RooFit.LineStyle( 9), RooFit.VLines());

        if self.higgs_sample=="ggH1000":
            model_pdf_ggH.plotOn(mplot,RooFit.Normalization(scale_number_ggH*signal_scale),RooFit.Name("ggH#times%s, m_{H}=1TeV"%(signal_scale)),RooFit.DrawOption("L"), RooFit.LineColor(self.color_palet["ggH"]), RooFit.LineStyle(2), RooFit.VLines());
            model_pdf_vbfH.plotOn(mplot,RooFit.Normalization(scale_number_vbfH*signal_scale),RooFit.Name("qqH#times%s, m_{H}=1TeV"%(signal_scale)),RooFit.DrawOption("L"), RooFit.LineColor(self.color_palet["vbfH"]), RooFit.LineStyle( 9), RooFit.VLines());

        data_obs.plotOn(mplot, RooFit.Name("data"), RooFit.MarkerSize(1.5), RooFit.DataError(RooAbsData.SumW2), RooFit.XErrorSize(0) );
        model_Total_background_MC.plotOn(mplot,RooFit.Normalization(scale_number_Total_background_MC),RooFit.Invisible());
        mplot_pull = self.get_pull(rrv_x,mplot);
        
        self.FloatingParams.Print("v");
        if options.closuretest==0:
            draw_error_band(model_Total_background_MC, rrv_x.GetName(), rrv_number_Total_background_MC,self.FloatingParams,workspace ,mplot,self.color_palet["Uncertainty"],"F");
        else:
            draw_error_band(model_Total_background_MC, rrv_x.GetName(), rrv_number_Total_background_MC,self.FloatingParams,workspace ,mplot,self.color_palet["Uncertainty"],"F");

        mplot.Print();
        self.leg=self.legend4Plot(mplot,0, 1,0.05,0,0.1 );
        mplot.addObject(self.leg);
        mplot.GetYaxis().SetRangeUser(1e-2,mplot.GetMaximum()*1.3);

        datahist = data_obs.binnedClone(data_obs.GetName()+"_binnedClone",data_obs.GetName()+"_binnedClone")
        Nbin = int(rrv_x.getBins()); 
        nparameters = self.FloatingParams.getSize();        
        ChiSquare = model_Total_background_MC.createChi2(datahist,RooFit.Extended(kTRUE),RooFit.DataError(RooAbsData.Poisson));
        chi_over_ndf= ChiSquare.getVal()/(Nbin - nparameters);
        ## Add Chisquare to mplot_pull
        cs = TLatex(0.75,0.8,"#chi^{2}/ndf = %0.2f "%(float(chi_over_ndf)));
        cs.SetNDC();
        cs.SetTextSize(0.12);
        cs.AppendPad("same");
        mplot_pull.addObject(cs)

        print "nPar=%s, chiSquare=%s/%s"%(nparameters, ChiSquare.getVal()*(Nbin - nparameters), (Nbin - nparameters) );

        parameters_list = RooArgList();
        self.draw_canvas_with_pull( mplot, mplot_pull,parameters_list,"plots_%s_%s_%s_%s_g1/m_lvj_fitting/"%(options.additioninformation, self.channel,self.PS_model, self.wtagger_label),"check_workspace_for_limit_%s_%s"%(self.channel,self.higgs_sample),"",0,1);


    ### in order to get the pull
    def get_pull(self, rrv_x, mplot_orig):

        print "############### draw the pull plot ########################"
        hpull = mplot_orig.pullHist();
        x = ROOT.Double(0.); y = ROOT.Double(0) ;
        for ipoint in range(0,hpull.GetN()):
           hpull.GetPoint(ipoint,x,y);
           if(y == 0):
            hpull.SetPoint(ipoint,x,10)
       
        mplot_pull = rrv_x.frame(RooFit.Title("Pull Distribution"), RooFit.Bins(int(rrv_x.getBins()/self.narrow_factor)));
        medianLine = TLine(rrv_x.getMin(),0.,rrv_x.getMax(),0); medianLine.SetLineWidth(2); medianLine.SetLineColor(kRed);
        mplot_pull.addObject(medianLine);
        mplot_pull.addPlotable(hpull,"P");
        mplot_pull.SetTitle("");
        mplot_pull.GetXaxis().SetTitle("");
        mplot_pull.GetYaxis().SetRangeUser(-5,5);
        mplot_pull.GetYaxis().SetTitleSize(0.10);
        mplot_pull.GetYaxis().SetLabelSize(0.10);
        mplot_pull.GetXaxis().SetTitleSize(0.10);
        mplot_pull.GetXaxis().SetLabelSize(0.10);
        mplot_pull.GetYaxis().SetTitleOffset(0.40);
        mplot_pull.GetYaxis().SetTitle("#frac{data-fit}{#sigma_{data}}");
        mplot_pull.GetYaxis().CenterTitle();

        return mplot_pull;

    #### in order to make the banner on the plots
    def banner4Plot(self, iswithpull=0):
      print "############### draw the banner ########################"

      if iswithpull:
       if self.channel=="el":
        banner = TLatex(0.3,0.96,("CMS Preliminary, %.1f fb^{-1} at #sqrt{s} = 8 TeV, W#rightarrow e #nu "%(self.GetLumi())));
       elif self.channel=="mu":
        banner = TLatex(0.3,0.96,("CMS Preliminary, %.1f fb^{-1} at #sqrt{s} = 8 TeV, W#rightarrow #mu #nu "%(self.GetLumi())));
       elif self.channel=="em":
        banner = TLatex(0.3,0.96,("CMS Preliminary, %.1f fb^{-1} at #sqrt{s} = 8 TeV, W#rightarrow #mu,e #nu "%(self.GetLumi())));
       banner.SetNDC(); banner.SetTextSize(0.04);
      else:
       if self.channel=="el":
        banner = TLatex(0.22,0.96,("CMS Preliminary, %.1f fb^{-1} at #sqrt{s} = 8 TeV, W#rightarrow e #nu "%(self.GetLumi())));
       if self.channel=="mu":
        banner = TLatex(0.22,0.96,("CMS Preliminary, %.1f fb^{-1} at #sqrt{s} = 8 TeV, W#rightarrow #mu #nu "%(self.GetLumi())));
       if self.channel=="em":
        banner = TLatex(0.22,0.96,("CMS Preliminary, %.1f fb^{-1} at #sqrt{s} = 8 TeV, W#rightarrow #mu,e #nu "%(self.GetLumi())));
       banner.SetNDC(); banner.SetTextSize(0.033);
                                                                                                         
      return banner;


    ### in order to make the legend
    def legend4Plot(self, plot, left=1, isFill=1, x_offset_low=0., y_offset_low=0., x_offset_high =0., y_offset_high =0., TwoCoulum =1.):
        print "############### draw the legend ########################"
        if left==-1:
            theLeg = TLegend(0.65+x_offset_low, 0.58+y_offset_low, 0.93+x_offset_low, 0.87+y_offset_low, "", "NDC");
            theLeg.SetName("theLegend");
            theLeg.SetLineColor(0);
            theLeg.SetTextFont(42);
            theLeg.SetTextSize(.04);
        else:
            theLeg = TLegend(0.41+x_offset_low, 0.61+y_offset_low, 0.76+x_offset_high, 0.93+y_offset_high, "", "NDC");
            theLeg.SetName("theLegend");
            if TwoCoulum :
                theLeg.SetNColumns(2);

        theLeg.SetFillColor(0);
        theLeg.SetFillStyle(0);
        theLeg.SetBorderSize(0);
        theLeg.SetLineColor(0);
        theLeg.SetLineWidth(0);
        theLeg.SetLineStyle(0);
        theLeg.SetTextSize(0.040);
        theLeg.SetTextFont(42);

        entryCnt = 0;
        objName_before = "";
        objName_signal_graviton = "";
        objNameLeg_signal_graviton = "";

        if self.channel=="mu": legHeader="(#mu#nu, 2JHP)";
        else: legHeader="(e#nu, 2JHP)";

        for obj in range(int(plot.numItems()) ):
          objName = plot.nameOf(obj);
          if objName == "error_up" or objName == "error_dn" : continue ;
          if objName == "errorband" : objName = "Uncertainty";
          print objName;
          if not ( ( (plot.getInvisible(objName)) and (not TString(objName).Contains("Uncertainty")) ) or TString(objName).Contains("invisi") or TString(objName).Contains("TLine") or objName ==objName_before ):
            theObj = plot.getObject(obj);
            objTitle = objName;
            drawoption= plot.getDrawOptions(objName).Data()
            if drawoption=="P":drawoption="PE"
            if TString(objName).Contains("Uncertainty") or TString(objName).Contains("sigma"): objName_before=objName; continue ;
            elif TString(objName).Contains("Graph") : objName_before=objName; continue ;
            elif TString(objName).Data()=="data" : theLeg.AddEntry(theObj, "CMS Data "+legHeader,"PE"); objName_before=objName;
            else: objName_before=objName; continue ;

        entryCnt = 0;
        objName_before = "";
        objName_signal_graviton = "";
        objNameLeg_signal_graviton = "";
                   
        for obj in range(int(plot.numItems()) ):
          objName = plot.nameOf(obj);
          if objName == "error_up" or objName == "error_dn" : continue ;
          if objName == "errorband" : objName = "Uncertainty";
          print objName;
          if not ( ( (plot.getInvisible(objName)) and (not TString(objName).Contains("Uncertainty")) ) or TString(objName).Contains("invisi") or TString(objName).Contains("TLine") or objName ==objName_before ):
            theObj = plot.getObject(obj);
            objTitle = objName;
            drawoption= plot.getDrawOptions(objName).Data()
            if drawoption=="P":drawoption="PE"
            if TString(objName).Contains("Uncertainty") or TString(objName).Contains("sigma"): objName_before=objName; continue ;
            elif TString(objName).Contains("Graph") : objName_before=objName; continue ;
            elif TString(objName).Data()=="WJets" : theLeg.AddEntry(theObj, "W+jets","F"); objName_before=objName;
            else: objName_before=objName; continue ;

        entryCnt = 0;
        objName_before = "";
        objName_signal_graviton = "";
        objNameLeg_signal_graviton = "";


        for obj in range(int(plot.numItems()) ):
            objName = plot.nameOf(obj);
            if objName == "error_up" or objName == "error_dn" : continue ;
            if objName == "errorband" : objName = "Uncertainty";
            print objName;
            if not ( ( (plot.getInvisible(objName)) and (not TString(objName).Contains("Uncertainty")) ) or TString(objName).Contains("invisi") or TString(objName).Contains("TLine") or objName ==objName_before ):
                theObj = plot.getObject(obj);
                objTitle = objName;
                drawoption= plot.getDrawOptions(objName).Data()
                if drawoption=="P":drawoption="PE"
                if TString(objName).Contains("Uncertainty") or TString(objName).Contains("sigma"):
                    theLeg.AddEntry(theObj, objName,"F");
                elif TString(objName).Contains("Graph") :
                    if not (objName_before=="Graph" or objName_before=="Uncertainty"): theLeg.AddEntry(theObj, "Uncertainty","F");
                else:
                    if TString(objName).Data()=="STop" : theLeg.AddEntry(theObj, "Single Top","F");
                    elif TString(objName).Data()=="TTbar" : theLeg.AddEntry(theObj, "t#bar{t}","F");
                    elif TString(objName).Data()=="VV" : theLeg.AddEntry(theObj, "WW/WZ","F");
                    elif TString(objName).Data()=="data" : objName_before=objName; entryCnt = entryCnt+1; continue ;
                    elif TString(objName).Data()=="WJets" : objName_before=objName; entryCnt = entryCnt+1; continue;
                    elif TString(objName).Contains("vbfH"): theLeg.AddEntry(theObj, (TString(objName).ReplaceAll("vbfH","qqH")).Data() ,"L");
                    elif TString(objName).Contains("Uncertainty"): theLeg.AddEntry(theObj, objTitle,drawoption);
                    elif TString(objName).Contains("Bulk"):
                       if TString(objName).Contains("BulkG_WW_inclusive_c0p2_M600") or TString(objName).Contains("BulkG_WW_lvjj_c0p2_M600"):
                           objName_signal_graviton = theObj ;
                           objNameLeg_signal_graviton = "Bulk G* M_{G*}=0.6 TeV #tilde{k}=0.5 (#times100)";
                       if TString(objName).Contains("BulkG_WW_inclusive_c0p2_M700") or TString(objName).Contains("BulkG_WW_lvjj_c0p2_M700"):
                           objName_signal_graviton = theObj ;
                           objNameLeg_signal_graviton = "Bulk G* M_{G*}=0.7 TeV #tilde{k}=0.5 (#times100)";
                       if TString(objName).Contains("BulkG_WW_inclusive_c0p2_M800") or TString(objName).Contains("BulkG_WW_lvjj_c0p2_M800"):
                           objName_signal_graviton = theObj ;
                           objNameLeg_signal_graviton = "Bulk G* M_{G*}=0.8 TeV #tilde{k}=0.5 (#times100)";
                       if TString(objName).Contains("BulkG_WW_inclusive_c0p2_M900") or TString(objName).Contains("BulkG_WW_lvjj_c0p2_M900"):
                           objName_signal_graviton = theObj ;
                           objNameLeg_signal_graviton = "Bulk G* M_{G*}=0.9 TeV #tilde{k}=0.5 (#times100)";
                       if TString(objName).Contains("BulkG_WW_inclusive_c0p2_M1000") or TString(objName).Contains("BulkG_WW_lvjj_c0p2_M1000"):
                           objName_signal_graviton = theObj ;
                           objNameLeg_signal_graviton = "Bulk G* M_{G*}=1 TeV #tilde{k}=0.5 (#times100)";
                       if TString(objName).Contains("BulkG_WW_inclusive_c0p2_M1100") or TString(objName).Contains("BulkG_WW_lvjj_c0p2_M1100"):
                           objName_signal_graviton = theObj ;
                           objNameLeg_signal_graviton = "Bulk G* M_{G*}=1.1 TeV #tilde{k}=0.5 (#times100)";
                       if TString(objName).Contains("BulkG_WW_inclusive_c0p2_M1200") or TString(objName).Contains("BulkG_WW_lvjj_c0p2_M1200"):
                           objName_signal_graviton = theObj ;
                           objNameLeg_signal_graviton = "Bulk G* M_{G*}=1.2 TeV #tilde{k}=0.5 (#times100)";
                       if TString(objName).Contains("BulkG_WW_inclusive_c0p2_M1300") or TString(objName).Contains("BulkG_WW_lvjj_c0p2_M1300"):
                           objName_signal_graviton = theObj ;
                           objNameLeg_signal_graviton = "Bulk G* M_{G*}=1.3 TeV #tilde{k}=0.5 (#times100)";
                       if TString(objName).Contains("BulkG_WW_inclusive_c0p2_M1400") or TString(objName).Contains("BulkG_WW_lvjj_c0p2_M1400"):
                           objName_signal_graviton = theObj ;
                           objNameLeg_signal_graviton = "Bulk G* M_{G*}=1.4 TeV #tilde{k}=0.5 (#times100)";
                       if TString(objName).Contains("BulkG_WW_inclusive_c0p2_M1500") or TString(objName).Contains("BulkG_WW_lvjj_c0p2_M1500"):
                           objName_signal_graviton = theObj ;
                           objNameLeg_signal_graviton = "Bulk G* M_{G*}=1.5 TeV #tilde{k}=0.5 (#times100)";
                       if TString(objName).Contains("BulkG_WW_inclusive_c0p2_M1600") or TString(objName).Contains("BulkG_WW_lvjj_c0p2_M1600"):
                           objName_signal_graviton = theObj ;
                           objNameLeg_signal_graviton = "Bulk G* M_{G*}=1.6 TeV #tilde{k}=0.5 (#times100)";
                       if TString(objName).Contains("BulkG_WW_inclusive_c0p2_M1700") or TString(objName).Contains("BulkG_WW_lvjj_c0p2_M1700"):
                           objName_signal_graviton = theObj ;
                           objNameLeg_signal_graviton = "Bulk G* M_{G*}=1.7 TeV #tilde{k}=0.5 (#times100)";
                       if TString(objName).Contains("BulkG_WW_inclusive_c0p2_M1800") or TString(objName).Contains("BulkG_WW_lvjj_c0p2_M1800"):
                           objName_signal_graviton = theObj ;
                           objNameLeg_signal_graviton = "Bulk G* M_{G*}=1.8 TeV #tilde{k}=0.5 (#times100)";
                       if TString(objName).Contains("BulkG_WW_inclusive_c0p2_M1900") or TString(objName).Contains("BulkG_WW_lvjj_c0p2_M1900"):
                           objName_signal_graviton = theObj ;
                           objNameLeg_signal_graviton = "Bulk G* M_{G*}=1.9 TeV #tilde{k}=0.5 (#times100)";
                       if TString(objName).Contains("BulkG_WW_inclusive_c0p2_M2000") or TString(objName).Contains("BulkG_WW_lvjj_c0p2_M2000"):
                           objName_signal_graviton = theObj ;
                           objNameLeg_signal_graviton = "Bulk G* M_{G*}=2 TeV #tilde{k}=0.5 (#times100)";
                       if TString(objName).Contains("BulkG_WW_inclusive_c0p2_M2100") or TString(objName).Contains("BulkG_WW_lvjj_c0p2_M2100"):
                           objName_signal_graviton = theObj ;
                           objNameLeg_signal_graviton = "Bulk G* M_{G*}=2.1 TeV #tilde{k}=0.5 (#times100)";
                       if TString(objName).Contains("BulkG_WW_inclusive_c0p2_M2200") or TString(objName).Contains("BulkG_WW_lvjj_c0p2_M2200"):
                           objName_signal_graviton = theObj ;
                           objNameLeg_signal_graviton = "Bulk G* M_{G*}=2.2 TeV #tilde{k}=0.5 (#times100)";
                       if TString(objName).Contains("BulkG_WW_inclusive_c0p2_M2300") or TString(objName).Contains("BulkG_WW_lvjj_c0p2_M2300"):
                           objName_signal_graviton = theObj ;
                           objNameLeg_signal_graviton = "Bulk G* M_{G*}=2.3 TeV #tilde{k}=0.5 (#times100)";
                       if TString(objName).Contains("BulkG_WW_inclusive_c0p2_M2400") or TString(objName).Contains("BulkG_WW_lvjj_c0p2_M2400"):
                           objName_signal_graviton = theObj ;
                           objNameLeg_signal_graviton = "Bulk G* M_{G*}=2.4 TeV #tilde{k}=0.5 (#times100)";
                       if TString(objName).Contains("BulkG_WW_inclusive_c0p2_M2500") or TString(objName).Contains("BulkG_WW_lvjj_c0p2_M2500"):
                           objName_signal_graviton = theObj ;
                           objNameLeg_signal_graviton = "Bulk G* M_{G*}=2.5 TeV #tilde{k}=0.5 (#times100)";
                    else : theLeg.AddEntry(theObj, objTitle,drawoption);
                entryCnt=entryCnt+1;
            objName_before=objName;
        if objName_signal_graviton !="" :
           theLeg.AddEntry(objName_signal_graviton, TString(objNameLeg_signal_graviton).Data() ,"L");
        return theLeg;




    #### draw canvas with plots with pull
    def draw_canvas_with_pull(self, mplot, mplot_pull,parameters_list,in_directory, in_file_name, in_model_name="", show_constant_parameter=0, logy=0):# mplot + pull

        print "############### draw the canvas with pull ########################"
        mplot.GetXaxis().SetTitleOffset(1.1);
        mplot.GetYaxis().SetTitleOffset(1.3);
        mplot.GetXaxis().SetTitleSize(0.055);
        mplot.GetYaxis().SetTitleSize(0.055);
        mplot.GetXaxis().SetLabelSize(0.045);
        mplot.GetYaxis().SetLabelSize(0.045);
        mplot_pull.GetXaxis().SetLabelSize(0.14);
        mplot_pull.GetYaxis().SetLabelSize(0.14);
        mplot_pull.GetYaxis().SetTitleSize(0.15);
        mplot_pull.GetYaxis().SetNdivisions(205);

                                                                          
        cMassFit = TCanvas("cMassFit","cMassFit", 600,600);
        # if parameters_list is empty, don't draw pad3
        par_first=parameters_list.createIterator();
        par_first.Reset();
        param_first=par_first.Next()
        doParameterPlot = 0 ;
        if param_first and doParameterPlot != 0:
         pad1=TPad("pad1","pad1",0.,0. ,0.8,0.24);
         pad2=TPad("pad2","pad2",0.,0.24,0.8,1. );
         pad3=TPad("pad3","pad3",0.8,0.,1,1);
         pad1.Draw();
         pad2.Draw();
         pad3.Draw();
        else:
         pad1=TPad("pad1","pad1",0.,0. ,0.99,0.24);
         pad2=TPad("pad2","pad2",0.,0.24,0.99,1. );
         pad1.Draw();
         pad2.Draw();
                                                                                                                                                                              
        pad2.cd();
        mplot.Draw();
        banner = self.banner4Plot(1);
        banner.Draw();

        pad1.cd();
        mplot_pull.Draw();

        if param_first and doParameterPlot != 0:

            pad3.cd();
            latex=TLatex();
            latex.SetTextSize(0.1);
            par=parameters_list.createIterator();
            par.Reset();
            param=par.Next()
            i=0;
            while param:
                if (not param.isConstant() ) or show_constant_parameter:
                    param.Print();
                    icolor=1;#if a paramenter is constant, color is 2
                    if param.isConstant(): icolor=2
                    latex.DrawLatex(0,0.9-i*0.04,"#color[%s]{%s}"%(icolor,param.GetName()) );
                    latex.DrawLatex(0,0.9-i*0.04-0.02," #color[%s]{%4.3e +/- %2.1e}"%(icolor,param.getVal(),param.getError()) );
                    i=i+1;
                param=par.Next();

        ## create the directory where store the plots
        Directory = TString(in_directory+self.higgs_sample+"_%02d_%02d/"%(options.cprime,options.BRnew));
        if not Directory.EndsWith("/"):Directory = Directory.Append("/");
        if not os.path.isdir(Directory.Data()):
              os.system("mkdir -p "+Directory.Data());

        rlt_file = TString(Directory.Data()+in_file_name);
        if rlt_file.EndsWith(".root"):
            TString(in_model_name).ReplaceAll(".root","");
            rlt_file.ReplaceAll(".root","_"+in_model_name+"_with_pull.png");
        else:
            TString(in_model_name).ReplaceAll(".root","");
            rlt_file.ReplaceAll(".root","");
            rlt_file=rlt_file.Append("_"+in_model_name+"_with_pull.png");

        cMassFit.SaveAs(rlt_file.Data());

        rlt_file.ReplaceAll(".png",".pdf");
        cMassFit.SaveAs(rlt_file.Data());
        
        rlt_file.ReplaceAll(".pdf",".root");
        cMassFit.SaveAs(rlt_file.Data());

        string_file_name = TString(in_file_name);
        if string_file_name.EndsWith(".root"):
            string_file_name.ReplaceAll(".root","_"+in_model_name);
        else:
            string_file_name.ReplaceAll(".root","");
            string_file_name.Append("_"+in_model_name);

        if logy:
            mplot.GetYaxis().SetRangeUser(1e-3,mplot.GetMaximum()*200);
            pad2.SetLogy() ;
            pad2.Update();
            cMassFit.Update();
            rlt_file.ReplaceAll(".root","_log.root");
            cMassFit.SaveAs(rlt_file.Data());
            rlt_file.ReplaceAll(".root",".pdf");
            cMassFit.SaveAs(rlt_file.Data());
            rlt_file.ReplaceAll(".pdf",".png");
            cMassFit.SaveAs(rlt_file.Data());

        self.draw_canvas(mplot,in_directory,string_file_name.Data(),0,logy,1);

    #### jusr drawing canvas with no pull
    def draw_canvas(self, in_obj,in_directory, in_file_name, is_range=0, logy=0, frompull=0):

        print "############### draw the canvas without pull ########################"
        cMassFit = TCanvas("cMassFit","cMassFit", 600,600);

        if frompull and logy :
            in_obj.GetYaxis().SetRangeUser(1e-2,in_obj.GetMaximum()/200)
        elif not frompull and logy :
            in_obj.GetYaxis().SetRangeUser(0.00001,in_obj.GetMaximum())
            

        if is_range:
            h2=TH2D("h2","",100,400,1400,4,0.00001,4);
            h2.Draw();
            in_obj.Draw("same")
        else :
            in_obj.Draw()

        in_obj.GetXaxis().SetTitleSize(0.045);
        in_obj.GetXaxis().SetTitleOffset(1.15);
        in_obj.GetXaxis().SetLabelSize(0.04);

        in_obj.GetYaxis().SetTitleSize(0.055);
        in_obj.GetYaxis().SetTitleOffset(1.40);
        in_obj.GetYaxis().SetLabelSize(0.04);

        self.leg.SetTextSize(0.031);

        banner = self.banner4Plot();
        banner.Draw();
        
        Directory=TString(in_directory+self.higgs_sample+"_%02d_%02d/"%(options.cprime,options.BRnew));
        if not Directory.EndsWith("/"):Directory=Directory.Append("/");
        if not os.path.isdir(Directory.Data()):
              os.system("mkdir -p "+Directory.Data());

        rlt_file=TString(Directory.Data()+in_file_name);
        if rlt_file.EndsWith(".root"):
            rlt_file.ReplaceAll(".root","_rlt_without_pull_and_paramters.png");
        else:
            rlt_file.ReplaceAll(".root","");
            rlt_file = rlt_file.Append(".png");

        cMassFit.SaveAs(rlt_file.Data());

        rlt_file.ReplaceAll(".png",".pdf");
        cMassFit.SaveAs(rlt_file.Data());

        rlt_file.ReplaceAll(".pdf",".root");
        cMassFit.SaveAs(rlt_file.Data());

        if logy:
            in_obj.GetYaxis().SetRangeUser(1e-3,in_obj.GetMaximum()*200);
            cMassFit.SetLogy() ;
            cMassFit.Update();
            rlt_file.ReplaceAll(".root","_log.root");
            cMassFit.SaveAs(rlt_file.Data());
            rlt_file.ReplaceAll(".root",".pdf");
            cMassFit.SaveAs(rlt_file.Data());
            rlt_file.ReplaceAll(".pdf",".png");
            cMassFit.SaveAs(rlt_file.Data());
       


    ##### Get Lumi for banner title
    def GetLumi(self):

        if self.channel=="el": return 19.3;
        elif self.channel=="mu": return 19.3;
        elif self.channel=="em": return 19.3;                                                         


    ######## +++++++++++
    def get_data(self, signal_model="CB_v1"):
        print "############### get_data ########################"
        self.get_mj_and_mlvj_dataset(self.file_data,"_data")     
        getattr(self.workspace4limit_,"import")(self.workspace4fit_.var("rrv_number_dataset_signal_region_data_%s_mlvj"%(self.channel)).clone("observation_for_counting"))
 

    #### Define the steps to fit signal distribution in the mj and mlvj spectra
    def fit_Signal(self):
        print "############# fit_Signal #################"
        ### Build the dataset
        self.get_mj_and_mlvj_dataset(self.file_ggH,"_%s"%(self.higgs_sample));
        self.get_mj_and_mlvj_dataset(self.file_vbfH,"_%s"%(self.vbfhiggs_sample));

        
        if self.higgs_sample=="ggH600":
            self.fit_mlvj_model_single_MC(self.file_ggH,"_%smassvbf_jes_up"%(self.higgs_sample),"_signal_region","CB_v1",0,0,0,0,"_%s"%(self.higgs_sample));
            self.fit_mlvj_model_single_MC(self.file_ggH,"_%smassvbf_jes_dn"%(self.higgs_sample),"_signal_region","CB_v1",0,0,0,0,"_%s"%(self.higgs_sample));
            self.fit_mlvj_model_single_MC(self.file_ggH,"_%smassvbf_jer"%(self.higgs_sample),"_signal_region","CB_v1",0,0,0,0,"_%s"%(self.higgs_sample));
            self.fit_mlvj_model_single_MC(self.file_ggH,"_%smassvbf_jer_up"%(self.higgs_sample),"_signal_region","CB_v1",0,0,0,0,"_%s"%(self.higgs_sample));
            self.fit_mlvj_model_single_MC(self.file_ggH,"_%smassvbf_jer_dn"%(self.higgs_sample),"_signal_region","CB_v1",0,0,0,0,"_%s"%(self.higgs_sample));
            self.fit_mlvj_model_single_MC(self.file_ggH,"_%s"%(self.higgs_sample),"_signal_region","CB_v1",0,0,0,0,"_%s"%(self.higgs_sample));

            self.fit_mlvj_model_single_MC(self.file_vbfH,"_%smassvbf_jes_up"%(self.vbfhiggs_sample),"_signal_region","CB_v1",0,0,0,0,"_%s"%(self.vbfhiggs_sample));
            self.fit_mlvj_model_single_MC(self.file_vbfH,"_%smassvbf_jes_dn"%(self.vbfhiggs_sample),"_signal_region","CB_v1",0,0,0,0,"_%s"%(self.vbfhiggs_sample));
            self.fit_mlvj_model_single_MC(self.file_vbfH,"_%smassvbf_jer"%(self.vbfhiggs_sample),"_signal_region","CB_v1",0,0,0,0,"_%s"%(self.vbfhiggs_sample));
            self.fit_mlvj_model_single_MC(self.file_vbfH,"_%smassvbf_jer_up"%(self.vbfhiggs_sample),"_signal_region","CB_v1",0,0,0,0,"_%s"%(self.vbfhiggs_sample));
            self.fit_mlvj_model_single_MC(self.file_vbfH,"_%smassvbf_jer_dn"%(self.vbfhiggs_sample),"_signal_region","CB_v1",0,0,0,0,"_%s"%(self.vbfhiggs_sample));
            self.fit_mlvj_model_single_MC(self.file_vbfH,"_%s"%(self.vbfhiggs_sample),"_signal_region","CB_v1",0,0,0,0,"_%s"%(self.vbfhiggs_sample));

        elif self.higgs_sample=="ggH700":
            self.fit_mlvj_model_single_MC(self.file_ggH,"_%smassvbf_jes_up"%(self.higgs_sample),"_signal_region","CB_v1",0,0,0,0,"_%s"%(self.higgs_sample));
            self.fit_mlvj_model_single_MC(self.file_ggH,"_%smassvbf_jes_dn"%(self.higgs_sample),"_signal_region","CB_v1",0,0,0,0,"_%s"%(self.higgs_sample));
            self.fit_mlvj_model_single_MC(self.file_ggH,"_%smassvbf_jer"%(self.higgs_sample),"_signal_region","CB_v1",0,0,0,0,"_%s"%(self.higgs_sample));
            self.fit_mlvj_model_single_MC(self.file_ggH,"_%smassvbf_jer_up"%(self.higgs_sample),"_signal_region","CB_v1",0,0,0,0,"_%s"%(self.higgs_sample));
            self.fit_mlvj_model_single_MC(self.file_ggH,"_%smassvbf_jer_dn"%(self.higgs_sample),"_signal_region","CB_v1",0,0,0,0,"_%s"%(self.higgs_sample));
            self.fit_mlvj_model_single_MC(self.file_ggH,"_%s"%(self.higgs_sample),"_signal_region","CB_v1",0,0,0,0,"_%s"%(self.higgs_sample));

            self.fit_mlvj_model_single_MC(self.file_vbfH,"_%smassvbf_jes_up"%(self.vbfhiggs_sample),"_signal_region","CB_v1",0,0,0,0,"_%s"%(self.vbfhiggs_sample));
            self.fit_mlvj_model_single_MC(self.file_vbfH,"_%smassvbf_jes_dn"%(self.vbfhiggs_sample),"_signal_region","CB_v1",0,0,0,0,"_%s"%(self.vbfhiggs_sample));
            self.fit_mlvj_model_single_MC(self.file_vbfH,"_%smassvbf_jer"%(self.vbfhiggs_sample),"_signal_region","CB_v1",0,0,0,0,"_%s"%(self.vbfhiggs_sample));
            self.fit_mlvj_model_single_MC(self.file_vbfH,"_%smassvbf_jer_up"%(self.vbfhiggs_sample),"_signal_region","CB_v1",0,0,0,0,"_%s"%(self.vbfhiggs_sample));
            self.fit_mlvj_model_single_MC(self.file_vbfH,"_%smassvbf_jer_dn"%(self.vbfhiggs_sample),"_signal_region","CB_v1",0,0,0,0,"_%s"%(self.vbfhiggs_sample));
            self.fit_mlvj_model_single_MC(self.file_vbfH,"_%s"%(self.vbfhiggs_sample),"_signal_region","CB_v1",0,0,0,0,"_%s"%(self.vbfhiggs_sample));

        elif self.higgs_sample=="ggH800":
            self.fit_mlvj_model_single_MC(self.file_ggH,"_%smassvbf_jes_up"%(self.higgs_sample),"_signal_region","CB_v1",0,0,0,0,"_%s"%(self.higgs_sample));
            self.fit_mlvj_model_single_MC(self.file_ggH,"_%smassvbf_jes_dn"%(self.higgs_sample),"_signal_region","CB_v1",0,0,0,0,"_%s"%(self.higgs_sample));
            self.fit_mlvj_model_single_MC(self.file_ggH,"_%smassvbf_jer"%(self.higgs_sample),"_signal_region","CB_v1",0,0,0,0,"_%s"%(self.higgs_sample));
            self.fit_mlvj_model_single_MC(self.file_ggH,"_%smassvbf_jer_up"%(self.higgs_sample),"_signal_region","CB_v1",0,0,0,0,"_%s"%(self.higgs_sample));
            self.fit_mlvj_model_single_MC(self.file_ggH,"_%smassvbf_jer_dn"%(self.higgs_sample),"_signal_region","CB_v1",0,0,0,0,"_%s"%(self.higgs_sample));
            self.fit_mlvj_model_single_MC(self.file_ggH,"_%s"%(self.higgs_sample),"_signal_region","CB_v1",0,0,0,0,"_%s"%(self.higgs_sample));

            self.fit_mlvj_model_single_MC(self.file_vbfH,"_%smassvbf_jes_up"%(self.vbfhiggs_sample),"_signal_region","CB_v1",0,0,0,0,"_%s"%(self.vbfhiggs_sample));
            self.fit_mlvj_model_single_MC(self.file_vbfH,"_%smassvbf_jes_dn"%(self.vbfhiggs_sample),"_signal_region","CB_v1",0,0,0,0,"_%s"%(self.vbfhiggs_sample));
            self.fit_mlvj_model_single_MC(self.file_vbfH,"_%smassvbf_jer"%(self.vbfhiggs_sample),"_signal_region","CB_v1",0,0,0,0,"_%s"%(self.vbfhiggs_sample));
            self.fit_mlvj_model_single_MC(self.file_vbfH,"_%smassvbf_jer_up"%(self.vbfhiggs_sample),"_signal_region","CB_v1",0,0,0,0,"_%s"%(self.vbfhiggs_sample));
            self.fit_mlvj_model_single_MC(self.file_vbfH,"_%smassvbf_jer_dn"%(self.vbfhiggs_sample),"_signal_region","CB_v1",0,0,0,0,"_%s"%(self.vbfhiggs_sample));
            self.fit_mlvj_model_single_MC(self.file_vbfH,"_%s"%(self.vbfhiggs_sample),"_signal_region","CB_v1",0,0,0,0,"_%s"%(self.vbfhiggs_sample));

        elif self.higgs_sample=="ggH900":
            self.fit_mlvj_model_single_MC(self.file_ggH,"_%smassvbf_jes_up"%(self.higgs_sample),"_signal_region","CB_v1",0,0,0,0,"_%s"%(self.higgs_sample));
            self.fit_mlvj_model_single_MC(self.file_ggH,"_%smassvbf_jes_dn"%(self.higgs_sample),"_signal_region","CB_v1",0,0,0,0,"_%s"%(self.higgs_sample));
            self.fit_mlvj_model_single_MC(self.file_ggH,"_%smassvbf_jer"%(self.higgs_sample),"_signal_region","CB_v1",0,0,0,0,"_%s"%(self.higgs_sample));
            self.fit_mlvj_model_single_MC(self.file_ggH,"_%smassvbf_jer_up"%(self.higgs_sample),"_signal_region","CB_v1",0,0,0,0,"_%s"%(self.higgs_sample));
            self.fit_mlvj_model_single_MC(self.file_ggH,"_%smassvbf_jer_dn"%(self.higgs_sample),"_signal_region","CB_v1",0,0,0,0,"_%s"%(self.higgs_sample));
            self.fit_mlvj_model_single_MC(self.file_ggH,"_%s"%(self.higgs_sample),"_signal_region","CB_v1",0,0,0,0,"_%s"%(self.higgs_sample));

            self.fit_mlvj_model_single_MC(self.file_vbfH,"_%smassvbf_jes_up"%(self.vbfhiggs_sample),"_signal_region","CB_v1",0,0,0,0,"_%s"%(self.vbfhiggs_sample));
            self.fit_mlvj_model_single_MC(self.file_vbfH,"_%smassvbf_jes_dn"%(self.vbfhiggs_sample),"_signal_region","CB_v1",0,0,0,0,"_%s"%(self.vbfhiggs_sample));
            self.fit_mlvj_model_single_MC(self.file_vbfH,"_%smassvbf_jer"%(self.vbfhiggs_sample),"_signal_region","CB_v1",0,0,0,0,"_%s"%(self.vbfhiggs_sample));
            self.fit_mlvj_model_single_MC(self.file_vbfH,"_%smassvbf_jer_up"%(self.vbfhiggs_sample),"_signal_region","CB_v1",0,0,0,0,"_%s"%(self.vbfhiggs_sample));
            self.fit_mlvj_model_single_MC(self.file_vbfH,"_%smassvbf_jer_dn"%(self.vbfhiggs_sample),"_signal_region","CB_v1",0,0,0,0,"_%s"%(self.vbfhiggs_sample));
            self.fit_mlvj_model_single_MC(self.file_vbfH,"_%s"%(self.vbfhiggs_sample),"_signal_region","CB_v1",0,0,0,0,"_%s"%(self.vbfhiggs_sample));

        elif self.higgs_sample=="ggH1000":
            self.fit_mlvj_model_single_MC(self.file_ggH,"_%smassvbf_jes_up"%(self.higgs_sample),"_signal_region","CB_v1",0,0,0,0,"_%s"%(self.higgs_sample));
            self.fit_mlvj_model_single_MC(self.file_ggH,"_%smassvbf_jes_dn"%(self.higgs_sample),"_signal_region","CB_v1",0,0,0,0,"_%s"%(self.higgs_sample));
            self.fit_mlvj_model_single_MC(self.file_ggH,"_%smassvbf_jer"%(self.higgs_sample),"_signal_region","CB_v1",0,0,0,0,"_%s"%(self.higgs_sample));
            self.fit_mlvj_model_single_MC(self.file_ggH,"_%smassvbf_jer_up"%(self.higgs_sample),"_signal_region","CB_v1",0,0,0,0,"_%s"%(self.higgs_sample));
            self.fit_mlvj_model_single_MC(self.file_ggH,"_%smassvbf_jer_dn"%(self.higgs_sample),"_signal_region","CB_v1",0,0,0,0,"_%s"%(self.higgs_sample));
            self.fit_mlvj_model_single_MC(self.file_ggH,"_%s"%(self.higgs_sample),"_signal_region","CB_v1",0,0,0,0,"_%s"%(self.higgs_sample));

            self.fit_mlvj_model_single_MC(self.file_vbfH,"_%smassvbf_jes_up"%(self.vbfhiggs_sample),"_signal_region","CB_v1",0,0,0,0,"_%s"%(self.vbfhiggs_sample));
            self.fit_mlvj_model_single_MC(self.file_vbfH,"_%smassvbf_jes_dn"%(self.vbfhiggs_sample),"_signal_region","CB_v1",0,0,0,0,"_%s"%(self.vbfhiggs_sample));
            self.fit_mlvj_model_single_MC(self.file_vbfH,"_%smassvbf_jer"%(self.vbfhiggs_sample),"_signal_region","CB_v1",0,0,0,0,"_%s"%(self.vbfhiggs_sample));
            self.fit_mlvj_model_single_MC(self.file_vbfH,"_%smassvbf_jer_up"%(self.vbfhiggs_sample),"_signal_region","CB_v1",0,0,0,0,"_%s"%(self.vbfhiggs_sample));
            self.fit_mlvj_model_single_MC(self.file_vbfH,"_%smassvbf_jer_dn"%(self.vbfhiggs_sample),"_signal_region","CB_v1",0,0,0,0,"_%s"%(self.vbfhiggs_sample));
            self.fit_mlvj_model_single_MC(self.file_vbfH,"_%s"%(self.vbfhiggs_sample),"_signal_region","CB_v1",0,0,0,0,"_%s"%(self.vbfhiggs_sample));
        
        print "________________________________________________________________________"
        
 
    ##### Define the steps to fit WJets MC in the mj and mlvj spectra
    def fit_WJets(self):
        print "######################### fit_WJets ########################"        
        self.get_mj_and_mlvj_dataset(self.file_WJets0_mc,"_WJets0")# to get the shape of m_lvj
        self.get_mj_and_mlvj_dataset(self.file_WJets0_mc,"_WJets01")# to get the shape of m_lvj


        self.fit_mj_single_MC(self.file_WJets0_mc,"_WJets0massvbf_jes_up","ErfExp");
        self.fit_mj_single_MC(self.file_WJets0_mc,"_WJets0massvbf_jes_dn","ErfExp");
        self.fit_mj_single_MC(self.file_WJets0_mc,"_WJets0massvbf_jer_up","ErfExp");
        self.fit_mj_single_MC(self.file_WJets0_mc,"_WJets0massvbf_jer","ErfExp");
        self.fit_mj_single_MC(self.file_WJets0_mc,"_WJets0massvbf_jer_dn","ErfExp");
        self.fit_mj_single_MC(self.file_WJets0_mc,"_WJets01","User1");# use for estimating the fitting model uncertainty
        self.fit_mj_single_MC(self.file_WJets0_mc,"_WJets0","ErfExp");# use for estimating the PS model uncertainty

        self.fit_mlvj_model_single_MC(self.file_WJets0_mc,"_WJets0massvbf_jes_up","_sb_lo",self.MODEL_4_mlvj,0,0,1,1,"_WJets0");
        self.fit_mlvj_model_single_MC(self.file_WJets0_mc,"_WJets0massvbf_jes_dn","_sb_lo",self.MODEL_4_mlvj,0,0,1,1,"_WJets0");
        self.fit_mlvj_model_single_MC(self.file_WJets0_mc,"_WJets0massvbf_jer_up","_sb_lo",self.MODEL_4_mlvj,0,0,1,1,"_WJets0");
        self.fit_mlvj_model_single_MC(self.file_WJets0_mc,"_WJets0massvbf_jer","_sb_lo",self.MODEL_4_mlvj,0,0,1,1,"_WJets0");
        self.fit_mlvj_model_single_MC(self.file_WJets0_mc,"_WJets0massvbf_jer_dn","_sb_lo",self.MODEL_4_mlvj,0,0,1,1,"_WJets0");
        self.fit_mlvj_model_single_MC(self.file_WJets0_mc,"_WJets01","_sb_lo",self.MODEL_4_mlvj_alter,1,0,1,1,"_WJets01");
        self.fit_mlvj_model_single_MC(self.file_WJets0_mc,"_WJets0","_sb_lo",self.MODEL_4_mlvj,1,0,1,1,"_WJets0");

        self.fit_mlvj_model_single_MC(self.file_WJets0_mc,"_WJets0massvbf_jes_up","_signal_region",self.MODEL_4_mlvj,0,0,1,1,"_WJets0");
        self.fit_mlvj_model_single_MC(self.file_WJets0_mc,"_WJets0massvbf_jes_dn","_signal_region",self.MODEL_4_mlvj,0,0,1,1,"_WJets0");
        self.fit_mlvj_model_single_MC(self.file_WJets0_mc,"_WJets0massvbf_jer_up","_signal_region",self.MODEL_4_mlvj,0,0,1,1,"_WJets0");
        self.fit_mlvj_model_single_MC(self.file_WJets0_mc,"_WJets0massvbf_jer","_signal_region",self.MODEL_4_mlvj,0,0,1,1,"_WJets0");
        self.fit_mlvj_model_single_MC(self.file_WJets0_mc,"_WJets0massvbf_jer_dn","_signal_region",self.MODEL_4_mlvj,0,0,1,1,"_WJets0");
        self.fit_mlvj_model_single_MC(self.file_WJets0_mc,"_WJets01","_signal_region",self.MODEL_4_mlvj_alter,1,0,1,1,"_WJets0");
        self.fit_mlvj_model_single_MC(self.file_WJets0_mc,"_WJets0","_signal_region",self.MODEL_4_mlvj,1,0,1,1,"_WJets0");


        print "________________________________________________________________________"

    ##### Define the steps to fit VV MC in the mj and mlvj spectra
    def fit_VV(self):
        print "############################# fit_VV ################################"

        ### Build the dataset        
        self.get_mj_and_mlvj_dataset(self.file_VV_mc,"_VV","jet_mass_pr")# to get the shape of m_lvj

        self.fit_mj_single_MC(self.file_VV_mc,"_VVmassvbf_jes_up","2_2Gaus");
        self.fit_mj_single_MC(self.file_VV_mc,"_VVmassvbf_jes_dn","2_2Gaus");        
        self.fit_mj_single_MC(self.file_VV_mc,"_VVmassvbf_jer","2_2Gaus");
        self.fit_mj_single_MC(self.file_VV_mc,"_VVmassvbf_jer_up","2_2Gaus");        
        self.fit_mj_single_MC(self.file_VV_mc,"_VVmassvbf_jer_dn","2_2Gaus");        
        self.fit_mj_single_MC(self.file_VV_mc,"_VV","2_2Gaus");                        

        self.fit_mlvj_model_single_MC(self.file_VV_mc,"_VVmassvbf_jes_up","_sb_lo",self.MODEL_4_mlvj,0,0,1,0,"_VV");
        self.fit_mlvj_model_single_MC(self.file_VV_mc,"_VVmassvbf_jes_dn","_sb_lo",self.MODEL_4_mlvj,0,0,1,0,"_VV");
        self.fit_mlvj_model_single_MC(self.file_VV_mc,"_VVmassvbf_jer","_sb_lo",self.MODEL_4_mlvj,0,0,1,0,"_VV");
        self.fit_mlvj_model_single_MC(self.file_VV_mc,"_VVmassvbf_jer_up","_sb_lo",self.MODEL_4_mlvj,0,0,1,0,"_VV");
        self.fit_mlvj_model_single_MC(self.file_VV_mc,"_VVmassvbf_jer_dn","_sb_lo",self.MODEL_4_mlvj,0,0,1,0,"_VV");
        self.fit_mlvj_model_single_MC(self.file_VV_mc,"_VV","_sb_lo",self.MODEL_4_mlvj,0,0,1,0,"_VV");

        self.fit_mlvj_model_single_MC(self.file_VV_mc,"_VVmassvbf_jes_up","_signal_region",self.MODEL_4_mlvj,0,0,1,0,"_VV");
        self.fit_mlvj_model_single_MC(self.file_VV_mc,"_VVmassvbf_jes_dn","_signal_region",self.MODEL_4_mlvj,0,0,1,0,"_VV");
        self.fit_mlvj_model_single_MC(self.file_VV_mc,"_VVmassvbf_jer","_signal_region",self.MODEL_4_mlvj,0,0,1,0,"_VV");
        self.fit_mlvj_model_single_MC(self.file_VV_mc,"_VVmassvbf_jer_up","_signal_region",self.MODEL_4_mlvj,0,0,1,0,"_VV");
        self.fit_mlvj_model_single_MC(self.file_VV_mc,"_VVmassvbf_jer_dn","_signal_region",self.MODEL_4_mlvj,0,0,1,0,"_VV");
        self.fit_mlvj_model_single_MC(self.file_VV_mc,"_VV","_signal_region",self.MODEL_4_mlvj,0,0,1,0,"_VV");


        print "________________________________________________________________________"


    ##### Define the steps to fit WW_EWK MC in the mj and mlvj spectra
    def fit_WW_EWK(self):
        print "############################# fit_WW_EWK ################################"

        ### Build the dataset        
        self.get_mj_and_mlvj_dataset(self.file_WW_EWK_mc,"_WW_EWK","jet_mass_pr")# to get the shape of m_lvj

        self.fit_mj_single_MC(self.file_WW_EWK_mc,"_WW_EWKmassvbf_jes_up","2_2Gaus");
        self.fit_mj_single_MC(self.file_WW_EWK_mc,"_WW_EWKmassvbf_jes_dn","2_2Gaus");        
        self.fit_mj_single_MC(self.file_WW_EWK_mc,"_WW_EWKmassvbf_jer","2_2Gaus");        
        self.fit_mj_single_MC(self.file_WW_EWK_mc,"_WW_EWKmassvbf_jer_up","2_2Gaus");        
        self.fit_mj_single_MC(self.file_WW_EWK_mc,"_WW_EWKmassvbf_jer_dn","2_2Gaus");        
        self.fit_mj_single_MC(self.file_WW_EWK_mc,"_WW_EWK","2_2Gaus");                        

        self.fit_mlvj_model_single_MC(self.file_WW_EWK_mc,"_WW_EWKmassvbf_jes_up","_sb_lo",self.MODEL_4_mlvj,0,0,1,0,"_WW_EWK");
        self.fit_mlvj_model_single_MC(self.file_WW_EWK_mc,"_WW_EWKmassvbf_jes_dn","_sb_lo",self.MODEL_4_mlvj,0,0,1,0,"_WW_EWK");
        self.fit_mlvj_model_single_MC(self.file_WW_EWK_mc,"_WW_EWKmassvbf_jer","_sb_lo",self.MODEL_4_mlvj,0,0,1,0,"_WW_EWK");
        self.fit_mlvj_model_single_MC(self.file_WW_EWK_mc,"_WW_EWKmassvbf_jer_up","_sb_lo",self.MODEL_4_mlvj,0,0,1,0,"_WW_EWK");
        self.fit_mlvj_model_single_MC(self.file_WW_EWK_mc,"_WW_EWKmassvbf_jer_dn","_sb_lo",self.MODEL_4_mlvj,0,0,1,0,"_WW_EWK");
        self.fit_mlvj_model_single_MC(self.file_WW_EWK_mc,"_WW_EWK","_sb_lo",self.MODEL_4_mlvj,0,0,1,0,"_WW_EWK");

        self.fit_mlvj_model_single_MC(self.file_WW_EWK_mc,"_WW_EWKmassvbf_jes_up","_signal_region",self.MODEL_4_mlvj,0,0,1,0,"_WW_EWK");
        self.fit_mlvj_model_single_MC(self.file_WW_EWK_mc,"_WW_EWKmassvbf_jes_dn","_signal_region",self.MODEL_4_mlvj,0,0,1,0,"_WW_EWK");
        self.fit_mlvj_model_single_MC(self.file_WW_EWK_mc,"_WW_EWKmassvbf_jer","_signal_region",self.MODEL_4_mlvj,0,0,1,0,"_WW_EWK");
        self.fit_mlvj_model_single_MC(self.file_WW_EWK_mc,"_WW_EWKmassvbf_jer_up","_signal_region",self.MODEL_4_mlvj,0,0,1,0,"_WW_EWK");
        self.fit_mlvj_model_single_MC(self.file_WW_EWK_mc,"_WW_EWKmassvbf_jer_dn","_signal_region",self.MODEL_4_mlvj,0,0,1,0,"_WW_EWK");
        self.fit_mlvj_model_single_MC(self.file_WW_EWK_mc,"_WW_EWK","_signal_region",self.MODEL_4_mlvj,0,0,1,0,"_WW_EWK");

 

        print "________________________________________________________________________"


    ##### Define the steps to fit TTbar MC in the mj and mlvj spectra
    def fit_TTbar(self):

        print "################################ fit_TTbar #########################################"
        ### Build the dataset

        self.get_mj_and_mlvj_dataset(self.file_TTbar_mc,"_TTbar")# to get the shape of m_lvj
        self.get_mj_and_mlvj_dataset(self.file_TTbar_mcanlo_mc,"_TTbar_mcanlo")# to get the shape of m_lvj

        self.fit_mj_single_MC(self.file_TTbar_mcanlo_mc,"_TTbar_mcanlomassvbf_jes_up","2Gaus_ErfExp");
        self.fit_mj_single_MC(self.file_TTbar_mcanlo_mc,"_TTbar_mcanlomassvbf_jes_dn","2Gaus_ErfExp");        
        self.fit_mj_single_MC(self.file_TTbar_mcanlo_mc,"_TTbar_mcanlomassvbf_jer","2Gaus_ErfExp");        
        self.fit_mj_single_MC(self.file_TTbar_mcanlo_mc,"_TTbar_mcanlomassvbf_jer_up","2Gaus_ErfExp");        
        self.fit_mj_single_MC(self.file_TTbar_mcanlo_mc,"_TTbar_mcanlomassvbf_jer_dn","2Gaus_ErfExp");        
        self.fit_mj_single_MC(self.file_TTbar_mcanlo_mc,"_TTbar_mcanlo","2Gaus_ErfExp");

        self.fit_mj_single_MC(self.file_TTbar_mc,"_TTbarmassvbf_jes_up","2Gaus_ErfExp");
        self.fit_mj_single_MC(self.file_TTbar_mc,"_TTbarmassvbf_jes_dn","2Gaus_ErfExp");        
        self.fit_mj_single_MC(self.file_TTbar_mc,"_TTbarmassvbf_jer","2Gaus_ErfExp");        
        self.fit_mj_single_MC(self.file_TTbar_mc,"_TTbarmassvbf_jer_up","2Gaus_ErfExp");        
        self.fit_mj_single_MC(self.file_TTbar_mc,"_TTbarmassvbf_jer_dn","2Gaus_ErfExp");        
        self.fit_mj_single_MC(self.file_TTbar_mc,"_TTbar","2Gaus_ErfExp");

        self.fit_mlvj_model_single_MC(self.file_TTbar_mcanlo_mc,"_TTbar_mcanlomassvbf_jes_up","_sb_lo",self.MODEL_4_mlvj,1,0,0,0,"_TTbar_mcanlo");
        self.fit_mlvj_model_single_MC(self.file_TTbar_mcanlo_mc,"_TTbar_mcanlomassvbf_jes_dn","_sb_lo",self.MODEL_4_mlvj,1,0,0,0,"_TTbar_mcanlo");
        self.fit_mlvj_model_single_MC(self.file_TTbar_mcanlo_mc,"_TTbar_mcanlomassvbf_jer","_sb_lo",self.MODEL_4_mlvj,1,0,0,0,"_TTbar_mcanlo");
        self.fit_mlvj_model_single_MC(self.file_TTbar_mcanlo_mc,"_TTbar_mcanlomassvbf_jer_up","_sb_lo",self.MODEL_4_mlvj,1,0,0,0,"_TTbar_mcanlo");
        self.fit_mlvj_model_single_MC(self.file_TTbar_mcanlo_mc,"_TTbar_mcanlomassvbf_jer_dn","_sb_lo",self.MODEL_4_mlvj,1,0,0,0,"_TTbar_mcanlo");
        self.fit_mlvj_model_single_MC(self.file_TTbar_mcanlo_mc,"_TTbar_mcanlo","_sb_lo",self.MODEL_4_mlvj,1,0,0,0,"_TTbar_mcanlo");

        self.fit_mlvj_model_single_MC(self.file_TTbar_mc,"_TTbarmassvbf_jes_up","_sb_lo",self.MODEL_4_mlvj,1,0,0,0,"_TTbar");
        self.fit_mlvj_model_single_MC(self.file_TTbar_mc,"_TTbarmassvbf_jes_dn","_sb_lo",self.MODEL_4_mlvj,1,0,0,0,"_TTbar");
        self.fit_mlvj_model_single_MC(self.file_TTbar_mc,"_TTbarmassvbf_jer","_sb_lo",self.MODEL_4_mlvj,1,0,0,0,"_TTbar");
        self.fit_mlvj_model_single_MC(self.file_TTbar_mc,"_TTbarmassvbf_jer_up","_sb_lo",self.MODEL_4_mlvj,1,0,0,0,"_TTbar");
        self.fit_mlvj_model_single_MC(self.file_TTbar_mc,"_TTbarmassvbf_jer_dn","_sb_lo",self.MODEL_4_mlvj,1,0,0,0,"_TTbar");
        self.fit_mlvj_model_single_MC(self.file_TTbar_mc,"_TTbar","_sb_lo",self.MODEL_4_mlvj,1,0,0,0,"_TTbar");

        self.fit_mlvj_model_single_MC(self.file_TTbar_mcanlo_mc,"_TTbar_mcanlomassvbf_jes_up","_signal_region",self.MODEL_4_mlvj,1,0,0,0,"_TTbar_mcanlo");
        self.fit_mlvj_model_single_MC(self.file_TTbar_mcanlo_mc,"_TTbar_mcanlomassvbf_jes_dn","_signal_region",self.MODEL_4_mlvj,1,0,0,0,"_TTbar_mcanlo");
        self.fit_mlvj_model_single_MC(self.file_TTbar_mcanlo_mc,"_TTbar_mcanlomassvbf_jer","_signal_region",self.MODEL_4_mlvj,1,0,0,0,"_TTbar_mcanlo");
        self.fit_mlvj_model_single_MC(self.file_TTbar_mcanlo_mc,"_TTbar_mcanlomassvbf_jer_up","_signal_region",self.MODEL_4_mlvj,1,0,0,0,"_TTbar_mcanlo");
        self.fit_mlvj_model_single_MC(self.file_TTbar_mcanlo_mc,"_TTbar_mcanlomassvbf_jer_dn","_signal_region",self.MODEL_4_mlvj,1,0,0,0,"_TTbar_mcanlo");
        self.fit_mlvj_model_single_MC(self.file_TTbar_mcanlo_mc,"_TTbar_mcanlo","_signal_region",self.MODEL_4_mlvj,1,0,0,0,"_TTbar_mcanlo");

        self.fit_mlvj_model_single_MC(self.file_TTbar_mc,"_TTbarmassvbf_jes_up","_signal_region",self.MODEL_4_mlvj,1,0,0,0,"_TTbar");
        self.fit_mlvj_model_single_MC(self.file_TTbar_mc,"_TTbarmassvbf_jes_dn","_signal_region",self.MODEL_4_mlvj,1,0,0,0,"_TTbar");
        self.fit_mlvj_model_single_MC(self.file_TTbar_mc,"_TTbarmassvbf_jer","_signal_region",self.MODEL_4_mlvj,1,0,0,0,"_TTbar");
        self.fit_mlvj_model_single_MC(self.file_TTbar_mc,"_TTbarmassvbf_jer_up","_signal_region",self.MODEL_4_mlvj,1,0,0,0,"_TTbar");
        self.fit_mlvj_model_single_MC(self.file_TTbar_mc,"_TTbarmassvbf_jer_dn","_signal_region",self.MODEL_4_mlvj,1,0,0,0,"_TTbar");
        self.fit_mlvj_model_single_MC(self.file_TTbar_mc,"_TTbar","_signal_region",self.MODEL_4_mlvj,1,0,0,0,"_TTbar");


        print "________________________________________________________________________"



    ##### Define the steps to fit TTbar MC in the mj and mlvj spectra
    def fit_STop(self):
        print "############################### fit_STop #########################################"
        ### Build the dataset
        self.get_mj_and_mlvj_dataset(self.file_STop_mc,"_STop")# to get the shape of m_lvj

        self.fit_mj_single_MC(self.file_STop_mc,"_STopmassvbf_jes_up","ErfExp");
        self.fit_mj_single_MC(self.file_STop_mc,"_STopmassvbf_jes_dn","ErfExp");        
        self.fit_mj_single_MC(self.file_STop_mc,"_STopmassvbf_jer","ErfExp");        
        self.fit_mj_single_MC(self.file_STop_mc,"_STopmassvbf_jer_up","ErfExp");        
        self.fit_mj_single_MC(self.file_STop_mc,"_STopmassvbf_jer_dn","ErfExp");        
        self.fit_mj_single_MC(self.file_STop_mc,"_STop","ErfExp");

        self.fit_mlvj_model_single_MC(self.file_STop_mc,"_STopmassvbf_jes_up","_sb_lo",self.MODEL_4_mlvj,0,0,0,0,"_STop");
        self.fit_mlvj_model_single_MC(self.file_STop_mc,"_STopmassvbf_jes_dn","_sb_lo",self.MODEL_4_mlvj,0,0,0,0,"_STop");
        self.fit_mlvj_model_single_MC(self.file_STop_mc,"_STopmassvbf_jer","_sb_lo",self.MODEL_4_mlvj,0,0,0,0,"_STop");
        self.fit_mlvj_model_single_MC(self.file_STop_mc,"_STopmassvbf_jer_up","_sb_lo",self.MODEL_4_mlvj,0,0,0,0,"_STop");
        self.fit_mlvj_model_single_MC(self.file_STop_mc,"_STopmassvbf_jer_dn","_sb_lo",self.MODEL_4_mlvj,0,0,0,0,"_STop");
        self.fit_mlvj_model_single_MC(self.file_STop_mc,"_STop","_sb_lo",self.MODEL_4_mlvj,0,0,0,0,"_STop");

        self.fit_mlvj_model_single_MC(self.file_STop_mc,"_STopmassvbf_jes_up","_signal_region",self.MODEL_4_mlvj,0,0,0,0,"_STop");
        self.fit_mlvj_model_single_MC(self.file_STop_mc,"_STopmassvbf_jes_dn","_signal_region",self.MODEL_4_mlvj,0,0,0,0,"_STop");
        self.fit_mlvj_model_single_MC(self.file_STop_mc,"_STopmassvbf_jer","_signal_region",self.MODEL_4_mlvj,0,0,0,0,"_STop");
        self.fit_mlvj_model_single_MC(self.file_STop_mc,"_STopmassvbf_jer_up","_signal_region",self.MODEL_4_mlvj,0,0,0,0,"_STop");
        self.fit_mlvj_model_single_MC(self.file_STop_mc,"_STopmassvbf_jer_dn","_signal_region",self.MODEL_4_mlvj,0,0,0,0,"_STop");
        self.fit_mlvj_model_single_MC(self.file_STop_mc,"_STop","_signal_region",self.MODEL_4_mlvj,0,0,0,0,"_STop");

        
        print "________________________________________________________________________"  


    ##### Fit of all the MC in both mj and mlvj : Signal, TTbar, STop, VV and Wjets
    def fit_AllSamples_Mj_and_Mlvj(self):
        print "################### fit_AllSamples_Mj_and_Mlvj #####################"
        self.fit_Signal();
        self.fit_STop();
        self.fit_VV();
        self.fit_WW_EWK();        
        self.fit_WJets();
        self.fit_TTbar();

        print "________________________________________________________________________"

                                                                    

    ##### Analysis with sideband alpha correction
    def analysis_sideband_correction_method1(self):
      print "##################### Start sideband correction full analysis ##############";
      ### Fit all MC components in both mj and mlvj
      self.fit_AllSamples_Mj_and_Mlvj();
      ### take the real data
      self.get_data();
      ### fit the WJets Normalization into the signal region -> no jet mass fluctuation has been done
      self.fit_WJetsNorm(1,0);
      ### fit data in the mlvj low sideband with two different models
      self.fit_mlvj_in_Mj_sideband("_WJets0massvbf_jes_up","_sb_lo", self.MODEL_4_mlvj,1,0);
      self.fit_mlvj_in_Mj_sideband("_WJets0massvbf_jes_dn","_sb_lo", self.MODEL_4_mlvj,1,0);
      self.fit_mlvj_in_Mj_sideband("_WJets0massvbf_jer","_sb_lo", self.MODEL_4_mlvj,1,0);
      self.fit_mlvj_in_Mj_sideband("_WJets0massvbf_jer_up","_sb_lo", self.MODEL_4_mlvj,1,0);
      self.fit_mlvj_in_Mj_sideband("_WJets0massvbf_jer_dn","_sb_lo", self.MODEL_4_mlvj,1,0);
      self.fit_mlvj_in_Mj_sideband("_WJets01","_sb_lo", self.MODEL_4_mlvj_alter,1,0);
      self.fit_mlvj_in_Mj_sideband("_WJets0","_sb_lo", self.MODEL_4_mlvj,1,0);

      ### Prepare the workspace and datacards
      self.prepare_limit("sideband_correction_method1",0,1)
      self.read_workspace()

    ####### +++++++++++++++
    def analysis_sideband_correction_method1_without_shape_and_psmodel_systermatic(self):
        self.fit_AllSamples_Mj_and_Mlvj()
        self.get_data()
        self.fit_WJetsNormalization_in_Mj_signal_region("_WJets0");
        self.fit_mlvj_in_Mj_sideband("_WJets0","_sb_lo", self.MODEL_4_mlvj,1)
        self.prepare_limit("sideband_correction_method1")
        self.read_workspace(1)


### funtion to run the analysis without systematics
def pre_limit_sb_correction_without_systermatic( channel, higgs_sample="HWWMH600", in_mlvj_signal_region_min=500, in_mlvj_signal_region_max=700, in_mj_min=30, in_mj_max=140, in_mlvj_min=400, in_mlvj_max=1400, fit_model="ErfExp_v1", fit_model_alter="ErfPow_v1"): # the WJets M_lvj shape and normalization are from sb_correction

    print "#################### pre_limit_sb_correction_without_systermatic: channel %s, signal %s, max and min signal region %f-%f, max and min mJ %f-%f, max and min mlvj %f-f, fit model %s and alternate %s ######################"%(channel,higgs_sample,in_mlvj_signal_region_min,in_mlvj_signal_region_max,in_mj_min,in_mj_max,in_mlvj_mi,in_mlvj_max,fit_model,fit_model_alter);

    boostedW_fitter=doFit_wj_and_wlvj(channel, higgs_sample, in_mlvj_signal_region_min, in_mlvj_signal_region_max, in_mj_min, in_mj_max, in_mlvj_min, in_mlvj_max,fit_model, fit_model_alter);
    boostedW_fitter.analysis_sideband_correction_method1_without_shape_and_psmodel_systermatic();


### funtion to run the complete alpha analysis
def pre_limit_sb_correction(method, channel, higgs_sample="HWWMH600", in_mlvj_signal_region_min=500, in_mlvj_signal_region_max=700, in_mj_min=30, in_mj_max=140, in_mlvj_min=400, in_mlvj_max=1400, fit_model="ErfExp_v1", fit_model_alter="ErfPow_v1"): # the WJets M_lvj shape and normalization are from sb_correction

    print "#################### pre_limit_sb_correction: channel %s, signal %s, max and min signal region %f-%f, max and min mJ %f-%f, max and min mlvj %f-%f, fit model %s and alternate %s ######################"%(channel,higgs_sample,in_mlvj_signal_region_min,in_mlvj_signal_region_max,in_mj_min,in_mj_max,in_mlvj_min,in_mlvj_max,fit_model,fit_model_alter);

    boostedW_fitter=doFit_wj_and_wlvj(channel, higgs_sample, in_mlvj_signal_region_min, in_mlvj_signal_region_max, in_mj_min, in_mj_max, in_mlvj_min, in_mlvj_max,fit_model, fit_model_alter);
    getattr(boostedW_fitter,"analysis_sideband_correction_%s"%(method) )();


### funtion to run the analysis without systematic
def pre_limit_simple(channel):
    print "######################### pre_limit_simple for %s sampel"%(channel)
    pre_limit_sb_correction_without_systermatic(channel, "ggH600",550, 700,40,130,400,1000,"ErfPowExp_v1","ErfPow2_v1");
    
### function to check the workspace once it has already created
def check_workspace(channel, higgs):
    boostedW_fitter = doFit_wj_and_wlvj(channel,higgs);
    boostedW_fitter.read_workspace()


####################################
######### Main Programme ###########
####################################    

                            
if __name__ == '__main__':

    channel=options.channel;#mu or el; default is mu;

    if options.check:
        print '################# check workspace for %s sample'%(channel);
        check_workspace(channel,"ggH600");

    if options.simple and ( not options.multi) and ( not options.check) :
        print '################# simple mode for %s sample'%(channel)
        pre_limit_simple(channel);

    if options.multi:
        print '################# multi mode for %s sample'%(channel)
        pre_limit_sb_correction("method1",sys.argv[1],sys.argv[2],int(sys.argv[3]),int(sys.argv[4]),int(sys.argv[5]),int(sys.argv[6]),int(sys.argv[7]),int(sys.argv[8]), sys.argv[9], sys.argv[10] );

#  LocalWords:  lvj
