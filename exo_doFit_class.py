#! /usr/bin/env python
import os
import glob
import math
import array
import ROOT
import ntpath

from ROOT import gROOT, TPaveLabel, gStyle, gSystem, TGaxis, TStyle, TLatex, TString, TF1,TFile,TLine, TLegend, TH1D,TH2D,THStack,TChain, TCanvas, TMatrixDSym, TMath, TText, TPad, RooFit, RooArgSet, RooArgList, RooArgSet, RooAbsData, RooAbsPdf, RooAddPdf, RooWorkspace, RooExtendPdf,RooCBShape, RooLandau, RooFFTConvPdf, RooGaussian, RooBifurGauss, RooArgusBG, RooDataSet, RooExponential,RooBreitWigner, RooVoigtian, RooNovosibirsk, RooRealVar,RooFormulaVar, RooDataHist, RooHistPdf,RooCategory, RooChebychev, RooSimultaneous, RooGenericPdf,RooConstVar, RooKeysPdf, RooHistPdf, RooEffProd, RooProdPdf, TIter, kTRUE, kFALSE, kGray, kRed, kDashed, kGreen,kAzure, kOrange, kBlack,kBlue,kYellow,kCyan, kMagenta, kWhite
import subprocess
from subprocess import Popen
from optparse import OptionParser


import sys

############################################
#            Job steering                  #
############################################

parser = OptionParser()

parser.add_option('-a', '--additioninformation',action="store",type="string",dest="additioninformation",default="EXO")
parser.add_option('-b', action='store_true', dest='noX', default=False, help='no X11 windows')
parser.add_option('-c', '--channel',action="store",type="string",dest="channel",default="el")

parser.add_option('-p', '--psmodel',action="store",type="string",dest="psmodel",default="pythia")
#parser.add_option('-p', '--psmodel',action="store",type="string",dest="psmodel",default="herwig")

parser.add_option('-s','--simple', action='store_true', dest='simple', default=True, help='pre-limit in simple mode')
parser.add_option('-m','--multi', action='store_true', dest='multi', default=False, help='pre-limit in multi mode')

parser.add_option('--check', action='store_true', dest='check', default=False, help='check the workspace for limit setting')
parser.add_option('--control', action='store_true', dest='control', default=False, help='control plot')
parser.add_option('--closuretest', action='store',type="int", dest='closuretest', default=0, help='closure test; 0: no test; 1: A1->A2; 2: A->B')

parser.add_option('--cprime', action="store",type="int",dest="cprime",default=10)
parser.add_option('--BRnew', action="store",type="int",dest="BRnew",default=0)
parser.add_option('--inPath', action="store",type="string",dest="inPath",default="./")

parser.add_option('--category', action="store",type="string",dest="category",default="HP")


(options, args) = parser.parse_args()
############################################################

ROOT.gSystem.Load(options.inPath+"/PDFs/HWWLVJRooPdfs_cxx.so")
ROOT.gSystem.Load(options.inPath+"/PDFs/PdfDiagonalizer_cc.so")
ROOT.gSystem.Load(options.inPath+"/PDFs/Util_cxx.so")

from ROOT import draw_error_band, draw_error_band_extendPdf, draw_error_band_Decor, draw_error_band_shape_Decor, Calc_error_extendPdf, Calc_error, RooErfExpPdf, RooAlpha, RooAlpha4ErfPowPdf, RooAlpha4ErfPow2Pdf, RooAlpha4ErfPowExpPdf, PdfDiagonalizer, RooPowPdf, RooPow2Pdf, RooErfPowExpPdf, RooErfPowPdf, RooErfPow2Pdf, RooQCDPdf, RooUser1Pdf, RooBWRunPdf, RooAnaExpNPdf, RooExpNPdf, RooAlpha4ExpNPdf, RooExpTailPdf, RooAlpha4ExpTailPdf, Roo2ExpPdf, RooAlpha42ExpPdf, RooGausExpPdf, RooAlpha4GausExpPdf



class doFit_wj_and_wlvj:
    def __init__(self, in_channel,in_signal_sample, in_mlvj_signal_region_min=500, in_mlvj_signal_region_max=700, in_mj_min=30, in_mj_max=140, in_mlvj_min=400., in_mlvj_max=1400., fit_model="ErfExp_v1", fit_model_alter="ErfPow_v1", input_workspace=None):

        self.setTDRStyle();#set plots style
        print "Begin to fit"

        RooAbsPdf.defaultIntegratorConfig().setEpsRel(1e-9) ;
        RooAbsPdf.defaultIntegratorConfig().setEpsAbs(1e-9) ;

        self.channel=in_channel;#el or muon
        self.signal_sample=in_signal_sample;
        self.MODEL_4_mlvj=fit_model;
        self.MODEL_4_mlvj_alter=fit_model_alter;

        #narrow the BinWidth_mj and BinWidth_mlvj by a factor of 5. Because Higgs-Combination-Tools will generate a binned sample, so need the bin width narrow. So, as a easy selution, we will increase the bin-width by a factor of 5 when ploting m_j m_WW

        if self.MODEL_4_mlvj=="ErfPowExp_v1" or self.MODEL_4_mlvj=="ErfPow2_v1" or self.MODEL_4_mlvj=="ErfExp_v1" or self.MODEL_4_mlvj=="GausExp_v1":
         self.BinWidth_mlvj=50.;
         self.narrow_factor=5.;
        else:
         self.BinWidth_mlvj=100.;
         self.narrow_factor=10.;

        self.BinWidth_mj=5.;
        
        self.BinWidth_mlvj=self.BinWidth_mlvj/self.narrow_factor;
        self.BinWidth_mj=self.BinWidth_mj/self.narrow_factor;
        nbins_mlvj=int((in_mlvj_max-in_mlvj_min)/self.BinWidth_mlvj);
        in_mlvj_max=in_mlvj_min+nbins_mlvj*self.BinWidth_mlvj;
        nbins_mj=int((in_mj_max-in_mj_min)/self.BinWidth_mj);
        in_mj_max=in_mj_min+nbins_mj*self.BinWidth_mj;

        rrv_mass_j  = RooRealVar("rrv_mass_j","Pruned jet mass",(in_mj_min+in_mj_max)/2.,in_mj_min,in_mj_max,"GeV");
        rrv_mass_j.setBins(nbins_mj);
        rrv_mass_lvj= RooRealVar("rrv_mass_lvj","m_{WW}",(in_mlvj_min+in_mlvj_max)/2.,in_mlvj_min,in_mlvj_max,"GeV");
        rrv_mass_lvj.setBins(nbins_mlvj);

        if input_workspace is None:
            self.workspace4fit_ = RooWorkspace("workspace4fit_","workspace4fit_");
        else:
            self.workspace4fit_ = input_workspace;
        getattr(self.workspace4fit_,"import")(rrv_mass_j);
        getattr(self.workspace4fit_,"import")(rrv_mass_lvj);

        #prepare workspace for unbin-Limit
        self.workspace4limit_ = RooWorkspace("workspace4limit_","workspace4limit_");

        if options.closuretest ==0:
            self.mj_sideband_lo_min=in_mj_min;
            self.mj_sideband_lo_max=65;
            self.mj_signal_min=65;
            self.mj_signal_max=105;
            self.mj_sideband_hi_min=105;
            self.mj_sideband_hi_max=in_mj_max;
        if options.closuretest ==1: ##closure test A1->A2
            self.mj_sideband_lo_min=in_mj_min;
            self.mj_sideband_lo_max=55;
            self.mj_signal_min=55;
            self.mj_signal_max= 65;
            self.mj_sideband_hi_min=105;
            self.mj_sideband_hi_max=in_mj_max;
        if options.closuretest ==2: #closure test A->B
            self.mj_sideband_lo_min=in_mj_min;
            self.mj_sideband_lo_max=65;
            self.mj_signal_min=100;
            self.mj_signal_max=115;
            self.mj_sideband_hi_min=115;
            self.mj_sideband_hi_max=in_mj_max;

        rrv_mass_j.setRange("sb_lo",self.mj_sideband_lo_min,self.mj_sideband_lo_max);
        rrv_mass_j.setRange("signal_region",self.mj_signal_min,self.mj_signal_max); 
        rrv_mass_j.setRange("sb_hi",self.mj_sideband_hi_min,self.mj_sideband_hi_max);
        rrv_mass_j.setRange("sblo_to_sbhi",self.mj_sideband_lo_min,self.mj_sideband_hi_max);
        rrv_mass_j.setRange("controlsample_fitting_range",40,130);

        self.mlvj_signal_min=in_mlvj_signal_region_min
        self.mlvj_signal_max=in_mlvj_signal_region_max
        rrv_mass_lvj.setRange("signal_region",self.mlvj_signal_min,self.mlvj_signal_max); 

        #prepare the data and mc files
        self.file_Directory="trainingtrees_exo_%s/"%(self.channel);

        self.PS_model= options.psmodel
        if options.closuretest ==0:
            #self.file_data=("ofile_pseudodata4exo.root");#keep blind!!!!
            self.file_data=("ofile_data.root");#keep blind!!!!
        else:#use true data to do the closuretest
            self.file_data=("ofile_data.root");#keep blind!!!!
        self.file_pseudodata=("ofile_pseudodata4exo.root");#fake data
        self.file_signal=("ofile_%s.root"%(self.signal_sample));

        #WJets0 is the default PS model, WJets1 is the alternative PS model
        if self.PS_model=="pythia":
            self.file_WJets0_mc=("ofile_WJets_Pythia180.root");
            self.file_WJets1_mc=("ofile_WJets_Herwig.root");
        else:
            self.file_WJets0_mc=("ofile_WJets_Herwig.root");
            self.file_WJets1_mc=("ofile_WJets_Pythia180.root");

        self.file_VV_mc=("ofile_VV.root");# WW+WZ 
        self.file_TTbar_mc=("ofile_TTbar_Powheg.root");
        self.file_TTbar_matchDn_mc=("ofile_TTbar_matchDn.root");
        self.file_TTbar_matchUp_mc=("ofile_TTbar_matchUp.root");
        self.file_TTbar_scaleDn_mc=("ofile_TTbar_scaleDn.root");
        self.file_TTbar_scaleUp_mc=("ofile_TTbar_scaleUp.root");
        self.file_TTbar_MG_mc=("ofile_TTbar_MG.root");
        self.file_STop_mc =("ofile_STop.root");#single Top

        self.wtagger_label=options.category;
        if self.wtagger_label=="HP" :
            if self.channel=="el":self.wtagger_cut=0.5   ; self.wtagger_cut_min=0.  ;
            if self.channel=="mu":self.wtagger_cut=0.5   ; self.wtagger_cut_min=0.  ;
        if self.wtagger_label=="LP": self.wtagger_cut=0.75  ; self.wtagger_cut_min=0.5 ;  
        if self.wtagger_label=="nocut": self.wtagger_cut=10000;

        #medium wtagger_eff reweight between data and mc
        if self.channel=="mu" and self.wtagger_label=="HP":
            self.rrv_wtagger_eff_reweight_forT=RooRealVar("rrv_wtagger_eff_reweight_forT","rrv_wtagger_eff_reweight_forT",0.986);
            self.rrv_wtagger_eff_reweight_forT.setError(0.034*self.rrv_wtagger_eff_reweight_forT.getVal());
            self.rrv_wtagger_eff_reweight_forV=RooRealVar("rrv_wtagger_eff_reweight_forV","rrv_wtagger_eff_reweight_forV",0.89);
            self.rrv_wtagger_eff_reweight_forV.setError(0.09*self.rrv_wtagger_eff_reweight_forV.getVal());

        if self.channel=="el" and self.wtagger_label=="HP":
            self.rrv_wtagger_eff_reweight_forT=RooRealVar("rrv_wtagger_eff_reweight_forT","rrv_wtagger_eff_reweight_forT",0.968);
            self.rrv_wtagger_eff_reweight_forT.setError(0.059*self.rrv_wtagger_eff_reweight_forT.getVal());
            self.rrv_wtagger_eff_reweight_forV=RooRealVar("rrv_wtagger_eff_reweight_forV","rrv_wtagger_eff_reweight_forV",1.004);
            self.rrv_wtagger_eff_reweight_forV.setError(0.12*self.rrv_wtagger_eff_reweight_forV.getVal());

        if self.channel=="mu" and self.wtagger_label=="LP":
            self.rrv_wtagger_eff_reweight_forT=RooRealVar("rrv_wtagger_eff_reweight_forT","rrv_wtagger_eff_reweight_forT",1.238);
            self.rrv_wtagger_eff_reweight_forT.setError(0.06*self.rrv_wtagger_eff_reweight_forT.getVal());
            self.rrv_wtagger_eff_reweight_forV=RooRealVar("rrv_wtagger_eff_reweight_forV","rrv_wtagger_eff_reweight_forV",1.301);
            self.rrv_wtagger_eff_reweight_forV.setError(0.27*self.rrv_wtagger_eff_reweight_forV.getVal());

        if self.channel=="el" and self.wtagger_label=="LP":
            self.rrv_wtagger_eff_reweight_forT=RooRealVar("rrv_wtagger_eff_reweight_forT","rrv_wtagger_eff_reweight_forT",1.337);
            self.rrv_wtagger_eff_reweight_forT.setError(0.082*self.rrv_wtagger_eff_reweight_forT.getVal());
            self.rrv_wtagger_eff_reweight_forV=RooRealVar("rrv_wtagger_eff_reweight_forV","rrv_wtagger_eff_reweight_forV",0.863);
            self.rrv_wtagger_eff_reweight_forV.setError(0.27*self.rrv_wtagger_eff_reweight_forV.getVal());

        print "wtagger efficiency correction for Top sample: %s +/- %s"%(self.rrv_wtagger_eff_reweight_forT.getVal(), self.rrv_wtagger_eff_reweight_forT.getError());
        print "wtagger efficiency correction for V   sample: %s +/- %s"%(self.rrv_wtagger_eff_reweight_forV.getVal(), self.rrv_wtagger_eff_reweight_forV.getError());

        self.mean_shift=1.5; self.sigma_scale=1.112; #correct the W-jet mass peak difference between data and MC



        
        #result files: The event number, parameters and error write into a txt file. The dataset and pdfs write into a root file
        if not os.path.isdir("cards_%s_%s_%s"%(options.additioninformation, self.channel,self.wtagger_label)):
            os.system("mkdir cards_%s_%s_%s"%(options.additioninformation, self.channel,self.wtagger_label));
        self.rlt_DIR="cards_%s_%s_%s/"%(options.additioninformation, self.channel,self.wtagger_label)

        self.file_rlt_txt           = self.rlt_DIR+"other_wwlvj_%s_%s_%s.txt"%(self.signal_sample,self.channel,self.wtagger_label)
        self.file_rlt_root          = self.rlt_DIR+"wwlvj_%s_%s_%02d_%02d_%s_workspace.root"%(self.signal_sample,self.channel,options.cprime,options.BRnew,self.wtagger_label)
        self.file_datacard_unbin    = self.rlt_DIR+"wwlvj_%s_%s_%02d_%02d_%s_unbin.txt"%(self.signal_sample,self.channel,options.cprime,options.BRnew,self.wtagger_label)
        self.file_datacard_counting = self.rlt_DIR+"wwlvj_%s_%s_%02d_%02d_%s_counting.txt"%(self.signal_sample,self.channel,options.cprime,options.BRnew,self.wtagger_label)
        
        self.file_out=open(self.file_rlt_txt,"w");
        self.file_out.write("Welcome:\n");
        self.file_out.close()
        self.file_out=open(self.file_rlt_txt,"a+");

        self.signal_xs_scale=1.0; #higgs XS scale
        
        self.color_palet={ #color palet
            'data'  : 1,
            'WJets' : 2,
            'VV'    : 4,
            'STop'  : 7,
            'TTbar' : 210,
            'ggH'   : 1,
            #'vbfH'  : kMagenta,
            'vbfH'  : 12,
            'Signal': 1,
            'Uncertainty' : kBlack,
            'Other_Backgrounds'  : kBlue
        }

        #PU study: 0-11,11-15,15-100
        self.nPV_min=  0;
        self.nPV_max= 300;
        self.vpt_cut= 200;
		#met cut:el 70; mu: 50
        self.pfMET_cut= 40;
        self.lpt_cut = 50;
        if self.channel=="el":
            self.pfMET_cut= 80; self.lpt_cut = 90;#very tight
        #deltaPhi_METj cut
        self.deltaPhi_METj_cut =2.0;

        # parameters of data-driven method to get the WJets background event number.
        self.number_WJets_insideband=-1;
        self.datadriven_alpha_WJets_unbin=-1;
        self.datadriven_alpha_WJets_counting=-1;

        #uncertainty for datacard
        self.lumi_uncertainty=0.044;  
        self.XS_STop_uncertainty =0.20 ; 
        self.XS_VV_uncertainty   =0.20 ;     
        self.XS_TTbar_NLO_uncertainty =0.063 ;# from AN-12-368 table8 
        self.XS_STop_NLO_uncertainty  =0.05 ;# from AN-12-368 table8 
        self.XS_VV_NLO_uncertainty    =0.10 ;# from AN-12-368 table8

        #normlization uncertainty from jet_mass
        self.WJets_normlization_uncertainty_from_jet_mass=0.;
        self.VV_normlization_uncertainty_from_jet_mass=0.;
        self.STop_normlization_uncertainty_from_jet_mass=0.;
        self.TTbar_normlization_uncertainty_from_jet_mass=0.;

        #el and mu trigger and eff uncertainty, AN2012_368_v5 12.3

        if self.channel == "mu":
           self.lep_trigger_uncertainty=0.01;
           self.lep_eff_uncertainty=0.01;
        else:
           self.lep_trigger_uncertainty=0.01;
           self.lep_eff_uncertainty=0.03;
            
        #b tag scale uncertainty
        self.btag_scale=1.0;
        self.btag_scale_uncertainty=0.025;

        self.signal_btag_uncertainty = 0.002 ;
      
        if self.channel == "mu":
         self.signal_lepton_energy_scale_uncertainty = 0.007 ;
         self.signal_lepton_energy_res_uncertainty = 0.001 ;
         self.signal_jet_energy_res_uncertainty = 0.003 ;
        else:
         self.signal_lepton_energy_scale_uncertainty = 0.002 ;
         self.signal_lepton_energy_res_uncertainty = 0.001 ;
         self.signal_jet_energy_res_uncertainty = 0.003 ;

        label_tstring=TString(self.signal_sample);
        if label_tstring.Contains("600") and (not label_tstring.Contains("1600")):
            self.signal_jet_energy_scale_uncertainty = 0.01 ;
        if label_tstring.Contains("700") and (not label_tstring.Contains("1700")):
            self.signal_jet_energy_scale_uncertainty = 0.011 ;
        if label_tstring.Contains("800") and (not label_tstring.Contains("1800")):
            self.signal_jet_energy_scale_uncertainty = 0.011 ;
        if label_tstring.Contains("900") and (not label_tstring.Contains("1900")):
            self.signal_jet_energy_scale_uncertainty = 0.011 ;
        if label_tstring.Contains("1000"):
            self.signal_jet_energy_scale_uncertainty = 0.011 ;
        if label_tstring.Contains("1100"):
            self.signal_jet_energy_scale_uncertainty = 0.014 ;
        if label_tstring.Contains("1200"):
            self.signal_jet_energy_scale_uncertainty = 0.014 ;
        if label_tstring.Contains("1300"):
            self.signal_jet_energy_scale_uncertainty = 0.014 ;
        if label_tstring.Contains("1400"):
            self.signal_jet_energy_scale_uncertainty = 0.014 ;
        if label_tstring.Contains("1500"):
            self.signal_jet_energy_scale_uncertainty = 0.015 ;
        if label_tstring.Contains("1600"):
            self.signal_jet_energy_scale_uncertainty = 0.015 ;
        if label_tstring.Contains("1700"):
            self.signal_jet_energy_scale_uncertainty = 0.016 ;
        if label_tstring.Contains("1800"):
            self.signal_jet_energy_scale_uncertainty = 0.016 ;
        if label_tstring.Contains("1900"):
            self.signal_jet_energy_scale_uncertainty = 0.018 ;
        if label_tstring.Contains("2000"):
            self.signal_jet_energy_scale_uncertainty = 0.018 ;
        if label_tstring.Contains("2100"):
            self.signal_jet_energy_scale_uncertainty = 0.02 ;
        if label_tstring.Contains("2200"):
            self.signal_jet_energy_scale_uncertainty = 0.02 ;
        if label_tstring.Contains("2300"):
            self.signal_jet_energy_scale_uncertainty = 0.023 ;
        if label_tstring.Contains("2400"):
            self.signal_jet_energy_scale_uncertainty = 0.026 ;
        if label_tstring.Contains("2500"):
            self.signal_jet_energy_scale_uncertainty = 0.03 ;

        # shape parameter uncertainty
        self.FloatingParams=RooArgList("floatpara_list");

    ##################### ---------------------------------------------------
    def setTDRStyle(self):
        self.tdrStyle =TStyle("tdrStyle","Style for P-TDR");
        #For the canvas:
        self.tdrStyle.SetCanvasBorderMode(0);
        self.tdrStyle.SetCanvasColor(kWhite);
        self.tdrStyle.SetCanvasDefH(600); #Height of canvas
        self.tdrStyle.SetCanvasDefW(600); #Width of canvas
        self.tdrStyle.SetCanvasDefX(0);   #POsition on screen
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
        self.tdrStyle.SetOptStat(0); #To display the mean and RMS:   SetOptStat("mr");
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
        self.tdrStyle.SetPadTickX(1);  #To get tick marks on the opposite side of the frame
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
        
        if in_model_name == "Voig":
            rrv_mean_voig=RooRealVar("rrv_mean_voig"+label+"_"+self.channel,"rrv_mean_voig"+label+"_"+self.channel,84,78,88);# W mass: 80.385
            rrv_width_voig=RooRealVar("rrv_width_voig"+label+"_"+self.channel,"rrv_width_voig"+label+"_"+self.channel,7.,1,40);
            rrv_sigma_voig=RooRealVar("rrv_sigma_voig"+label+"_"+self.channel,"rrv_sigma_voig"+label+"_"+self.channel,5,0.01,20);
            model_pdf = RooVoigtian("model_pdf"+label+"_"+self.channel+mass_spectrum,"model_pdf"+label+"_"+self.channel+mass_spectrum, rrv_x,rrv_mean_voig,rrv_width_voig,rrv_sigma_voig);

        if in_model_name == "Voig_v1":
            rrv_mean_voig=RooRealVar("rrv_mean_voig"+label+"_"+self.channel,"rrv_mean_voig"+label+"_"+self.channel,650,550,1200);# Higgs mass 600-1000
            rrv_width_voig=RooRealVar("rrv_width_voig"+label+"_"+self.channel,"rrv_width_voig"+label+"_"+self.channel,100.,10,600);
            rrv_sigma_voig=RooRealVar("rrv_sigma_voig"+label+"_"+self.channel,"rrv_sigma_voig"+label+"_"+self.channel,200,10,400);
            model_pdf = RooVoigtian("model_pdf"+label+"_"+self.channel+mass_spectrum,"model_pdf"+label+"_"+self.channel+mass_spectrum, rrv_x,rrv_mean_voig,rrv_width_voig,rrv_sigma_voig);

        if in_model_name == "Voig_v2":
            label_tstring=TString(label);

            # Bulk mass 600-1000
            
            if label_tstring.Contains("600") and (not  label_tstring.Contains("1600") ):                
             rrv_mean_voig=RooRealVar("rrv_mean_voig"+label+"_"+self.channel+"_"+self.wtagger_label,"rrv_mean_voig"+label+"_"+self.channel+"_"+self.wtagger_label,600,500,700);
             rrv_width_voig=RooRealVar("rrv_width_voig"+label+"_"+self.channel+"_"+self.wtagger_label,"rrv_width_voig"+label+"_"+self.channel+"_"+self.wtagger_label,2.5,0,10);
             rrv_width_voig.setConstant(kTRUE);
             rrv_sigma_voig=RooRealVar("rrv_sigma_voig"+label+"_"+self.channel+"_"+self.wtagger_label,"rrv_sigma_voig"+label+"_"+self.channel+"_"+self.wtagger_label,40,10,80);

            elif label_tstring.Contains("700") and (not  label_tstring.Contains("1700") ):                
             rrv_mean_voig=RooRealVar("rrv_mean_voig"+label+"_"+self.channel+"_"+self.wtagger_label,"rrv_mean_voig"+label+"_"+self.channel+"_"+self.wtagger_label,700,600,800);
             rrv_width_voig=RooRealVar("rrv_width_voig"+label+"_"+self.channel+"_"+self.wtagger_label,"rrv_width_voig"+label+"_"+self.channel+"_"+self.wtagger_label,2.5,0,10);
             rrv_width_voig.setConstant(kTRUE);
             rrv_sigma_voig=RooRealVar("rrv_sigma_voig"+label+"_"+self.channel+"_"+self.wtagger_label,"rrv_sigma_voig"+label+"_"+self.channel+"_"+self.wtagger_label,40,10,80);

            elif label_tstring.Contains("800") and (not  label_tstring.Contains("1800") ):                
             rrv_mean_voig=RooRealVar("rrv_mean_voig"+label+"_"+self.channel+"_"+self.wtagger_label,"rrv_mean_voig"+label+"_"+self.channel+"_"+self.wtagger_label,800,700,900);
             rrv_width_voig=RooRealVar("rrv_width_voig"+label+"_"+self.channel+"_"+self.wtagger_label,"rrv_width_voig"+label+"_"+self.channel+"_"+self.wtagger_label,2.5,0,10);
             rrv_width_voig.setConstant(kTRUE);
             rrv_sigma_voig=RooRealVar("rrv_sigma_voig"+label+"_"+self.channel+"_"+self.wtagger_label,"rrv_sigma_voig"+label+"_"+self.channel+"_"+self.wtagger_label,40,10,80);

            elif label_tstring.Contains("900") and (not  label_tstring.Contains("1900") ):                
             rrv_mean_voig=RooRealVar("rrv_mean_voig"+label+"_"+self.channel+"_"+self.wtagger_label,"rrv_mean_voig"+label+"_"+self.channel+"_"+self.wtagger_label,900,800,1000);
             rrv_width_voig=RooRealVar("rrv_width_voig"+label+"_"+self.channel+"_"+self.wtagger_label,"rrv_width_voig"+label+"_"+self.channel+"_"+self.wtagger_label,2.5,0,10);
             rrv_width_voig.setConstant(kTRUE);
             rrv_sigma_voig=RooRealVar("rrv_sigma_voig"+label+"_"+self.channel+"_"+self.wtagger_label,"rrv_sigma_voig"+label+"_"+self.channel+"_"+self.wtagger_label,40,10,90);

            elif label_tstring.Contains("1000"):
             rrv_mean_voig=RooRealVar("rrv_mean_voig"+label+"_"+self.channel+"_"+self.wtagger_label,"rrv_mean_voig"+label+"_"+self.channel+"_"+self.wtagger_label,1000,900,1100);
             rrv_width_voig=RooRealVar("rrv_width_voig"+label+"_"+self.channel+"_"+self.wtagger_label,"rrv_width_voig"+label+"_"+self.channel+"_"+self.wtagger_label,2.5,0,10);
             rrv_width_voig.setConstant(kTRUE);
             rrv_sigma_voig=RooRealVar("rrv_sigma_voig"+label+"_"+self.channel+"_"+self.wtagger_label,"rrv_sigma_voig"+label+"_"+self.channel+"_"+self.wtagger_label,40,10,80);
                
            model_pdf = RooVoigtian("model_pdf"+label+"_"+self.channel+mass_spectrum,"model_pdf"+label+"_"+self.channel+mass_spectrum, rrv_x,rrv_mean_voig,rrv_width_voig,rrv_sigma_voig);

        if in_model_name == "BW": 
            rrv_mean_BW=RooRealVar("rrv_mean_BW"+label+"_"+self.channel,"rrv_mean_BW"+label+"_"+self.channel,84,78, 88);
            rrv_width_BW=RooRealVar("rrv_width_BW"+label+"_"+self.channel,"rrv_width_BW"+label+"_"+self.channel,20,1,40);

            model_pdf = RooBreitWigner("model_pdf"+label+"_"+self.channel+mass_spectrum,"model_pdf"+label+"_"+self.channel+mass_spectrum, rrv_x,rrv_mean_BW,rrv_width_BW);

        if in_model_name == "BW_v1": 
            rrv_mean_BW=RooRealVar("rrv_mean_BW"+label+"_"+self.channel,"rrv_mean_BW"+label+"_"+self.channel,900,400, 1200);
            rrv_width_BW=RooRealVar("rrv_width_BW"+label+"_"+self.channel,"rrv_width_BW"+label+"_"+self.channel,400,200,800);
            model_pdf = RooBreitWigner("model_pdf"+label+"_"+self.channel+mass_spectrum,"model_pdf"+label+"_"+self.channel+mass_spectrum, rrv_x,rrv_mean_BW,rrv_width_BW);

        if in_model_name == "BWRUN":

            if label=="_ggH600_signal_region" or label=="_ggH600_sb_lo":
                rrv_mean_BWRUN = RooRealVar("rrv_mean_BWRUN"+label+"_"+self.channel,"rrv_mean_BWRUN"+label+"_"+self.channel,600,550,650);
                rrv_width_BWRUN= RooRealVar("rrv_width_BWRUN"+label+"_"+self.channel,"rrv_width_BWRUN"+label+"_"+self.channel,60,50,70);

            if label=="_ggH700_signal_region" or label=="_ggH700_sb_lo":
                rrv_mean_BWRUN = RooRealVar("rrv_mean_BWRUN"+label+"_"+self.channel,"rrv_mean_BWRUN"+label+"_"+self.channel,700,650,750);
                rrv_width_BWRUN= RooRealVar("rrv_width_BWRUN"+label+"_"+self.channel,"rrv_width_BWRUN"+label+"_"+self.channel,100,80,120);

            if label=="_ggH800_signal_region" or label=="_ggH800_sb_lo": 
                rrv_mean_BWRUN = RooRealVar("rrv_mean_BWRUN"+label+"_"+self.channel,"rrv_mean_BWRUN"+label+"_"+self.channel,800,750,850);
                rrv_width_BWRUN= RooRealVar("rrv_width_BWRUN"+label+"_"+self.channel,"rrv_width_BWRUN"+label+"_"+self.channel,150,100,180);

            if label=="_ggH900_signal_region" or label=="_ggH900_sb_lo": 
                rrv_mean_BWRUN = RooRealVar("rrv_mean_BWRUN"+label+"_"+self.channel,"rrv_mean_BWRUN"+label+"_"+self.channel,900,850,990);
                rrv_width_BWRUN= RooRealVar("rrv_width_BWRUN"+label+"_"+self.channel,"rrv_width_BWRUN"+label+"_"+self.channel,200,100,260);

            if label=="_ggH1000_signal_region" or label=="_ggH1000_sb_lo":
                rrv_mean_BWRUN = RooRealVar("rrv_mean_BWRUN"+label+"_"+self.channel,"rrv_mean_BWRUN"+label+"_"+self.channel,1000,950,1050);
                rrv_width_BWRUN= RooRealVar("rrv_width_BWRUN"+label+"_"+self.channel,"rrv_width_BWRUN"+label+"_"+self.channel,200,100,370); 

            bwrun = RooBWRunPdf("bwrun"+label+"_"+self.channel+mass_spectrum,"bwrun"+label+"_"+self.channel+mass_spectrum,rrv_x, rrv_mean_BWRUN, rrv_width_BWRUN);

            rrv_mean_cb = RooRealVar("rrv_mean_cb"+label+"_"+self.channel,"rrv_mean_cb"+label+"_"+self.channel,0);
            rrv_sigma_cb = RooRealVar("rrv_sigma_cb"+label+"_"+self.channel,"rrv_sigma_cb"+label+"_"+self.channel,50,10,300);
            rrv_alpha_cb = RooRealVar("rrv_alpha_cb"+label+"_"+self.channel,"rrv_alpha_cb"+label+"_"+self.channel,-3,-20,-1);
            rrv_n_cb = RooRealVar("rrv_n_cb"+label+"_"+self.channel,"rrv_n_cb"+label+"_"+self.channel,5,1,9);

            cbshape = RooGaussian("cbshape"+label+"_"+self.channel,"cbshape"+label+"_"+self.channel, rrv_x,rrv_mean_cb,rrv_sigma_cb);

            fft = RooFFTConvPdf("fft"+label+"_"+self.channel+mass_spectrum,"fft"+label+"_"+self.channel+mass_spectrum, rrv_x, bwrun, cbshape);

            rrv_offset_erf = RooRealVar("rrv_offset_erf"+label+"_"+self.channel,"rrv_offset_erf"+label+"_"+self.channel,450)#,350,550);
            rrv_width_erf = RooRealVar("rrv_width_erf"+label+"_"+self.channel,"rrv_width_erf"+label+"_"+self.channel,50)#,10,250);

            erf =  RooGenericPdf("erf"+label+"_"+self.channel+mass_spectrum,"erf"+label+"_"+self.channel+mass_spectrum, "(1.+TMath::Erf((%s-%s)/%s))/2."%( rrv_x.GetName(),rrv_offset_erf.GetName(), rrv_width_erf.GetName()), RooArgList(rrv_x,rrv_offset_erf,rrv_width_erf) )

            model_pdf = RooProdPdf("model_pdf"+label+"_"+self.channel+mass_spectrum,"model_pdf"+label+"_"+self.channel+mass_spectrum, fft, erf );
 
        if in_model_name == "2Voig":

            rrv_mean_voig=RooRealVar("rrv_mean_voig"+label+"_"+self.channel,"rrv_mean_voig"+label+"_"+self.channel,84,78,88);#W mass 80.385
            rrv_shift_2Voig=RooRealVar("rrv_shift_2Voig"+label+"_"+self.channel,"rrv_shift_2Voig"+label+"_"+self.channel,10.8026)   # Z mass: 91.1876;  shift=91.1876-80.385=10.8026
            rrv_mean_shifted= RooFormulaVar("rrv_mean_voig2"+label+"_"+self.channel,"@0+@1",RooArgList(rrv_mean_voig,rrv_shift_2Voig));
            rrv_width_voig=RooRealVar("rrv_width_voig"+label+"_"+self.channel,"rrv_width_voig"+label+"_"+self.channel,16.,6,26);
            #rrv_sigma_voig=RooRealVar("rrv_sigma_voig"+label+"_"+self.channel,"rrv_sigma_voig"+label+"_"+self.channel,2,0.5,5);
            rrv_sigma_voig=RooRealVar("rrv_sigma_voig"+label+"_"+self.channel,"rrv_sigma_voig"+label+"_"+self.channel,0.);
            rrv_frac=RooRealVar("rrv_frac"+label+"_"+self.channel,"rrv_frac"+label+"_"+self.channel,0.8,0.5,1.);
            model_voig1 = RooVoigtian("model_voig1"+label+"_"+self.channel+mass_spectrum,"model_voig1"+label+"_"+self.channel+mass_spectrum, rrv_x,rrv_mean_voig,rrv_width_voig,rrv_sigma_voig);
            model_voig2 = RooVoigtian("model_voig2"+label+"_"+self.channel+mass_spectrum,"model_voig2"+label+"_"+self.channel+mass_spectrum, rrv_x,rrv_mean_shifted,rrv_width_voig,rrv_sigma_voig);
            model_pdf = RooAddPdf("model_pdf"+label+"_"+self.channel+mass_spectrum,"model_pdf"+label+"_"+self.channel+mass_spectrum, RooArgList(model_voig1,model_voig2), RooArgList(rrv_frac));
    
        if in_model_name == "Gaus":

            label_tstring=TString(label);

            if label_tstring.Contains("600") and (not  label_tstring.Contains("1600") ):
             rrv_mean_gaus=RooRealVar("rrv_mean_gaus"+label+"_"+self.channel,"rrv_mean_gaus"+label+"_"+self.channel,600,500,700);# Bulk mass 600-1000
             rrv_sigma_gaus=RooRealVar("rrv_sigma_gaus"+label+"_"+self.channel,"rrv_sigma_gaus"+label+"_"+self.channel,40,10,80);

            elif label_tstring.Contains("700") and (not  label_tstring.Contains("1700") ):                
             rrv_mean_gaus=RooRealVar("rrv_mean_gaus"+label+"_"+self.channel,"rrv_mean_gaus"+label+"_"+self.channel,700,600,800);# Bulk mass 600-1000
             rrv_sigma_gaus=RooRealVar("rrv_sigma_gaus"+label+"_"+self.channel,"rrv_sigma_gaus"+label+"_"+self.channel,40,10,80);

            elif label_tstring.Contains("800") and (not  label_tstring.Contains("1800") ):                
             rrv_mean_gaus=RooRealVar("rrv_mean_gaus"+label+"_"+self.channel,"rrv_mean_gaus"+label+"_"+self.channel,800,700,900);# Bulk mass 600-1000
             rrv_sigma_gaus=RooRealVar("rrv_sigma_gaus"+label+"_"+self.channel,"rrv_sigma_gaus"+label+"_"+self.channel,40,10,80);

            elif label_tstring.Contains("900") and (not  label_tstring.Contains("1900") ):                
             rrv_mean_gaus=RooRealVar("rrv_mean_gaus"+label+"_"+self.channel,"rrv_mean_gaus"+label+"_"+self.channel,900,800,1000);# Bulk mass 600-1000
             rrv_sigma_gaus=RooRealVar("rrv_sigma_gaus"+label+"_"+self.channel,"rrv_sigma_gaus"+label+"_"+self.channel,40,10,90);

            if label_tstring.Contains("1000"):
             rrv_mean_gaus=RooRealVar("rrv_mean_gaus"+label+"_"+self.channel,"rrv_mean_gaus"+label+"_"+self.channel,1000,900,1100);# Bulk mass 600-1000
             rrv_sigma_gaus=RooRealVar("rrv_sigma_gaus"+label+"_"+self.channel,"rrv_sigma_gaus"+label+"_"+self.channel,40,10,80);

            elif label_tstring.Contains("1100"):
             rrv_mean_gaus=RooRealVar("rrv_mean_gaus"+label+"_"+self.channel,"rrv_mean_gaus"+label+"_"+self.channel,1100,1000,1200);# Bulk mass 600-1000
             rrv_sigma_gaus=RooRealVar("rrv_sigma_gaus"+label+"_"+self.channel,"rrv_sigma_gaus"+label+"_"+self.channel,40,10,100);

            elif label_tstring.Contains("1200"):
             rrv_mean_gaus=RooRealVar("rrv_mean_gaus"+label+"_"+self.channel,"rrv_mean_gaus"+label+"_"+self.channel,1200,1100,1300);# Bulk mass 600-1000
             rrv_sigma_gaus=RooRealVar("rrv_sigma_gaus"+label+"_"+self.channel,"rrv_sigma_gaus"+label+"_"+self.channel,40,10,100);

            else:
             rrv_mean_gaus=RooRealVar("rrv_mean_gaus"+label+"_"+self.channel,"rrv_mean_gaus"+label+"_"+self.channel,84,78,88);
             rrv_sigma_gaus=RooRealVar("rrv_sigma_gaus"+label+"_"+self.channel,"rrv_sigma_gaus"+label+"_"+self.channel,7,1,15);
                        
            model_pdf = RooGaussian("model_pdf"+label+"_"+self.channel+mass_spectrum,"model_pdf"+label+"_"+self.channel+mass_spectrum,rrv_x,rrv_mean_gaus,rrv_sigma_gaus);

        if in_model_name == "Gaus_v1":

            if label=="_ggH600_signal_region" or label=="_ggH600_sb_lo":
                rrv_mean_gaus=RooRealVar("rrv_mean_gaus"+label+"_"+self.channel,"rrv_mean_gaus"+label+"_"+self.channel,580,550,620);
                rrv_sigma_gaus=RooRealVar("rrv_sigma_gaus"+label+"_"+self.channel,"rrv_sigma_gaus"+label+"_"+self.channel,65,40,80);
            if label=="_ggH700_signal_region" or label=="_ggH700_sb_lo":
                rrv_mean_gaus=RooRealVar("rrv_mean_gaus"+label+"_"+self.channel,"rrv_mean_gaus"+label+"_"+self.channel,700,650,750);
                rrv_sigma_gaus=RooRealVar("rrv_sigma_gaus"+label+"_"+self.channel,"rrv_sigma_gaus"+label+"_"+self.channel,100,40,150);
            if label=="_ggH800_signal_region" or label=="_ggH800_sb_lo": 
                rrv_mean_gaus=RooRealVar("rrv_mean_gaus"+label+"_"+self.channel,"rrv_mean_gaus"+label+"_"+self.channel,800,750,850);
                rrv_sigma_gaus=RooRealVar("rrv_sigma_gaus"+label+"_"+self.channel,"rrv_sigma_gaus"+label+"_"+self.channel,130,120,140);
            if label=="_ggH900_signal_region" or label=="_ggH900_sb_lo": 
                rrv_mean_gaus=RooRealVar("rrv_mean_gaus"+label+"_"+self.channel,"rrv_mean_gaus"+label+"_"+self.channel,900,850,900);
                rrv_sigma_gaus=RooRealVar("rrv_sigma_gaus"+label+"_"+self.channel,"rrv_sigma_gaus"+label+"_"+self.channel,160,140,180);
            if label=="_ggH1000_signal_region" or label=="_ggH1000_sb_lo":
                rrv_mean_gaus=RooRealVar("rrv_mean_gaus"+label+"_"+self.channel,"rrv_mean_gaus"+label+"_"+self.channel,920,900,1000);
                rrv_sigma_gaus=RooRealVar("rrv_sigma_gaus"+label+"_"+self.channel,"rrv_sigma_gaus"+label+"_"+self.channel,200,100,300);
            model_pdf = RooGaussian("model_pdf"+label+"_"+self.channel+mass_spectrum,"model_pdf"+label+"_"+self.channel+mass_spectrum, rrv_x,rrv_mean_gaus,rrv_sigma_gaus);
 
        if in_model_name == "BifurGaus_v1":

            if label=="_ggH600_signal_region":
                rrv_mean_gaus=RooRealVar("rrv_mean_gaus"+label+"_"+self.channel,"rrv_mean_gaus"+label+"_"+self.channel,600,550,650);
                rrv_sigma1_gaus=RooRealVar("rrv_sigma1_gaus"+label+"_"+self.channel,"rrv_sigma1_gaus"+label+"_"+self.channel,67,40,80);
                rrv_sigma2_gaus=RooRealVar("rrv_sigma2_gaus"+label+"_"+self.channel,"rrv_sigma2_gaus"+label+"_"+self.channel,67,40,80);
            if label=="_ggH700_signal_region":
                rrv_mean_gaus=RooRealVar("rrv_mean_gaus"+label+"_"+self.channel,"rrv_mean_gaus"+label+"_"+self.channel,700,650,750);
                rrv_sigma1_gaus=RooRealVar("rrv_sigma1_gaus"+label+"_"+self.channel,"rrv_sigma1_gaus"+label+"_"+self.channel,100,40,150);
                rrv_sigma2_gaus=RooRealVar("rrv_sigma2_gaus"+label+"_"+self.channel,"rrv_sigma2_gaus"+label+"_"+self.channel,100,40,150);
            if label=="_ggH800_signal_region": 
                rrv_mean_gaus=RooRealVar("rrv_mean_gaus"+label+"_"+self.channel,"rrv_mean_gaus"+label+"_"+self.channel,800,750,850);
                rrv_sigma1_gaus=RooRealVar("rrv_sigma1_gaus"+label+"_"+self.channel,"rrv_sigma1_gaus"+label+"_"+self.channel,130,120,140);
                rrv_sigma2_gaus=RooRealVar("rrv_sigma2_gaus"+label+"_"+self.channel,"rrv_sigma2_gaus"+label+"_"+self.channel,130,120,140);
            if label=="_ggH900_signal_region": 
                rrv_mean_gaus=RooRealVar("rrv_mean_gaus"+label+"_"+self.channel,"rrv_mean_gaus"+label+"_"+self.channel,900,850,900);
                rrv_sigma1_gaus=RooRealVar("rrv_sigma1_gaus"+label+"_"+self.channel,"rrv_sigma1_gaus"+label+"_"+self.channel,160,140,180);
                rrv_sigma2_gaus=RooRealVar("rrv_sigma2_gaus"+label+"_"+self.channel,"rrv_sigma2_gaus"+label+"_"+self.channel,160,140,180);
            if label=="_ggH1000_signal_region":
                rrv_mean_gaus=RooRealVar("rrv_mean_gaus"+label+"_"+self.channel,"rrv_mean_gaus"+label+"_"+self.channel,920,900,1000);
                rrv_sigma1_gaus=RooRealVar("rrv_sigma1_gaus"+label+"_"+self.channel,"rrv_sigma1_gaus"+label+"_"+self.channel,200,100,300);
                rrv_sigma2_gaus=RooRealVar("rrv_sigma2_gaus"+label+"_"+self.channel,"rrv_sigma2_gaus"+label+"_"+self.channel,200,100,300);
            model_pdf = RooBifurGauss("model_pdf"+label+"_"+self.channel+mass_spectrum,"model_pdf"+label+"_"+self.channel+mass_spectrum, rrv_x,rrv_mean_gaus,rrv_sigma1_gaus,rrv_sigma2_gaus);
    
        if in_model_name == "CB":
            rrv_mean_CB=RooRealVar("rrv_mean_CB"+label+"_"+self.channel,"rrv_mean_CB"+label+"_"+self.channel,84,78,88);
            rrv_sigma_CB=RooRealVar("rrv_sigma_CB"+label+"_"+self.channel,"rrv_sigma_CB"+label+"_"+self.channel,7,4,10);
            rrv_alpha_CB=RooRealVar("rrv_alpha_CB"+label+"_"+self.channel,"rrv_alpha_CB"+label+"_"+self.channel,-2,-4,-0.5);
            rrv_n_CB=RooRealVar("rrv_n_CB"+label+"_"+self.channel,"rrv_n_CB"+label+"_"+self.channel,2,0.,4);
            model_pdf = RooCBShape("model_pdf"+label+"_"+self.channel+mass_spectrum,"model_pdf"+label+"_"+self.channel+mass_spectrum, rrv_x,rrv_mean_CB,rrv_sigma_CB,rrv_alpha_CB,rrv_n_CB);

        if in_model_name == "SCB_v1":
            rrv_mean_SCB=RooRealVar("rrv_mean_SCB"+label+"_"+self.channel,"rrv_mean_SCB"+label+"_"+self.channel,800,550,1000);
            rrv_sigma_SCB=RooRealVar("rrv_sigma_SCB"+label+"_"+self.channel,"rrv_sigma_SCB"+label+"_"+self.channel,70,40,300);
            rrv_alpha1_SCB=RooRealVar("rrv_alpha1_SCB"+label+"_"+self.channel,"rrv_alpha1_SCB"+label+"_"+self.channel,-2,-4,-0.5);
            rrv_alpha2_SCB=RooRealVar("rrv_alpha2_SCB"+label+"_"+self.channel,"rrv_alpha2_SCB"+label+"_"+self.channel,2,0.5,4);
            rrv_n1_SCB=RooRealVar("rrv_n1_SCB"+label+"_"+self.channel,"rrv_n1_SCB"+label+"_"+self.channel,2,0.,4);
            rrv_n2_SCB=RooRealVar("rrv_n2_SCB"+label+"_"+self.channel,"rrv_n2_SCB"+label+"_"+self.channel,2,0.,4);
            frac=RooRealVar("rrv_frac_SSCB"+label+"_"+self.channel,"rrv_frac_SSCB"+label+"_"+self.channel,0.5)
            scb1 = RooCBShape("model_pdf_scb1"+label+"_"+self.channel+mass_spectrum,"model_pdf_scb1"+label+"_"+self.channel+mass_spectrum, rrv_x,rrv_mean_SCB,rrv_sigma_SCB,rrv_alpha1_SCB,rrv_n1_SCB);
            scb2 = RooCBShape("model_pdf_scb2"+label+"_"+self.channel+mass_spectrum,"model_pdf_scb2"+label+"_"+self.channel+mass_spectrum, rrv_x,rrv_mean_SCB,rrv_sigma_SCB,rrv_alpha2_SCB,rrv_n2_SCB);
            model_pdf=RooAddPdf("model_pdf"+label+"_"+self.channel+mass_spectrum,"model_pdf"+label+"_"+self.channel+mass_spectrum,RooArgList(scb1,scb2),RooArgList(frac))

        if in_model_name == "2Gaus_sig":

            label_tstring=TString(label);
            if label_tstring.Contains("600") and (not  label_tstring.Contains("1600") ):
                rrv_mean1_gaus=RooRealVar("rrv_mean_1_gaus"+label+"_"+self.channel,"rrv_mean1_gaus"+label+"_"+self.channel, 600, 500, 700);
            elif label_tstring.Contains("700") and (not  label_tstring.Contains("1700") ):
                rrv_mean1_gaus=RooRealVar("rrv_mean_1_gaus"+label+"_"+self.channel,"rrv_mean1_gaus"+label+"_"+self.channel, 700, 600, 800);
            elif label_tstring.Contains("800") and (not  label_tstring.Contains("1800") ):
                rrv_mean1_gaus=RooRealVar("rrv_mean_1_gaus"+label+"_"+self.channel,"rrv_mean1_gaus"+label+"_"+self.channel, 800, 700, 900);
            elif label_tstring.Contains("900") and (not  label_tstring.Contains("1900") ):
                rrv_mean1_gaus=RooRealVar("rrv_mean_1_gaus"+label+"_"+self.channel,"rrv_mean1_gaus"+label+"_"+self.channel, 900, 800, 1000);
            elif label_tstring.Contains("1000"): rrv_mean1_gaus=RooRealVar("rrv_mean_1_gaus"+label+"_"+self.channel,"rrv_mean1_gaus"+label+"_"+self.channel, 1000, 900, 1100);
            elif label_tstring.Contains("1100"): rrv_mean1_gaus=RooRealVar("rrv_mean_1_gaus"+label+"_"+self.channel,"rrv_mean1_gaus"+label+"_"+self.channel, 1100, 1000, 1200);
            elif label_tstring.Contains("1200"): rrv_mean1_gaus=RooRealVar("rrv_mean_1_gaus"+label+"_"+self.channel,"rrv_mean1_gaus"+label+"_"+self.channel, 1200, 1100, 1300);
            elif label_tstring.Contains("1300"): rrv_mean1_gaus=RooRealVar("rrv_mean_1_gaus"+label+"_"+self.channel,"rrv_mean1_gaus"+label+"_"+self.channel, 1300, 1200, 1400);
            elif label_tstring.Contains("1400"): rrv_mean1_gaus=RooRealVar("rrv_mean_1_gaus"+label+"_"+self.channel,"rrv_mean1_gaus"+label+"_"+self.channel, 1400, 1300, 1500);
            elif label_tstring.Contains("1500"): rrv_mean1_gaus=RooRealVar("rrv_mean_1_gaus"+label+"_"+self.channel,"rrv_mean1_gaus"+label+"_"+self.channel, 1500, 1400, 1600);
            elif label_tstring.Contains("1600"): rrv_mean1_gaus=RooRealVar("rrv_mean_1_gaus"+label+"_"+self.channel,"rrv_mean1_gaus"+label+"_"+self.channel, 1600, 1500, 1700);
            elif label_tstring.Contains("1700"): rrv_mean1_gaus=RooRealVar("rrv_mean_1_gaus"+label+"_"+self.channel,"rrv_mean1_gaus"+label+"_"+self.channel, 1700, 1600, 1800);
            elif label_tstring.Contains("1800"): rrv_mean1_gaus=RooRealVar("rrv_mean_1_gaus"+label+"_"+self.channel,"rrv_mean1_gaus"+label+"_"+self.channel, 1800, 1700, 1900);
            elif label_tstring.Contains("1900"): rrv_mean1_gaus=RooRealVar("rrv_mean_1_gaus"+label+"_"+self.channel,"rrv_mean1_gaus"+label+"_"+self.channel, 1900, 1800, 2000);
            elif label_tstring.Contains("2000"): rrv_mean1_gaus=RooRealVar("rrv_mean_1_gaus"+label+"_"+self.channel,"rrv_mean1_gaus"+label+"_"+self.channel, 2000, 1900, 2100);
            elif label_tstring.Contains("2100"): rrv_mean1_gaus=RooRealVar("rrv_mean_1_gaus"+label+"_"+self.channel,"rrv_mean1_gaus"+label+"_"+self.channel, 2100, 2000, 2200);
            elif label_tstring.Contains("2200"): rrv_mean1_gaus=RooRealVar("rrv_mean_1_gaus"+label+"_"+self.channel,"rrv_mean1_gaus"+label+"_"+self.channel, 2200, 2100, 2300);
            elif label_tstring.Contains("2300"): rrv_mean1_gaus=RooRealVar("rrv_mean_1_gaus"+label+"_"+self.channel,"rrv_mean1_gaus"+label+"_"+self.channel, 2300, 2200, 2400);
            elif label_tstring.Contains("2400"): rrv_mean1_gaus=RooRealVar("rrv_mean_1_gaus"+label+"_"+self.channel,"rrv_mean1_gaus"+label+"_"+self.channel, 2400, 2300, 2500);
            elif label_tstring.Contains("2500"): rrv_mean1_gaus=RooRealVar("rrv_mean_1_gaus"+label+"_"+self.channel,"rrv_mean1_gaus"+label+"_"+self.channel, 2500, 2400, 2600);
            
            rrv_sigma1_gaus=RooRealVar("rrv_sigma1_gaus"+label+"_"+self.channel,"rrv_sigma1_gaus"+label+"_"+self.channel,50,20,120);
            gaus1 = RooGaussian("gaus1"+label+"_"+self.channel,"gaus1"+label+"_"+self.channel, rrv_x,rrv_mean1_gaus,rrv_sigma1_gaus);

            rrv_deltamean_gaus=RooRealVar("rrv_deltamean_gaus"+label+"_"+self.channel,"rrv_deltamean_gaus"+label+"_"+self.channel,0,-50,50); 
            rrv_mean2_gaus =RooFormulaVar("rrv_mean2_gaus"+label+"_"+self.channel,"@0+@1",RooArgList(rrv_mean1_gaus, rrv_deltamean_gaus));
            rrv_scalesigma_gaus=RooRealVar("rrv_scalesigma_gaus"+label+"_"+self.channel,"rrv_scalesigma_gaus"+label+"_"+self.channel,1,0.,10.); 
            rrv_sigma2_gaus=RooFormulaVar("rrv_sigma2_gaus"+label+"_"+self.channel,"@0*@1", RooArgList(rrv_sigma1_gaus,rrv_scalesigma_gaus));
            gaus2 = RooGaussian("gaus2"+label+"_"+self.channel,"gaus2"+label+"_"+self.channel, rrv_x,rrv_mean2_gaus,rrv_sigma2_gaus);
            rrv_frac = RooRealVar("rrv_frac"+label+"_"+self.channel,"rrv_frac"+label+"_"+self.channel,0.5,0.,1.);
            model_pdf =RooAddPdf("model_pdf"+label+"_"+self.channel+mass_spectrum,"model_pdf"+label+"_"+self.channel+mass_spectrum,RooArgList(gaus1,gaus2),RooArgList(rrv_frac),1)



        if in_model_name == "CB_v1":
            label_tstring=TString(label);
            if label_tstring.Contains("H600"): 
                rrv_mean_CB=RooRealVar("rrv_mean_CB"+label+"_"+self.channel+"_"+self.wtagger_label,"rrv_mean_CB"+label+"_"+self.channel+"_"+self.wtagger_label,600,580,620);
                rrv_sigma_CB=RooRealVar("rrv_sigma_CB"+label+"_"+self.channel+"_"+self.wtagger_label,"rrv_sigma_CB"+label+"_"+self.channel+"_"+self.wtagger_label,67,40,80);
                rrv_alpha_CB=RooRealVar("rrv_alpha_CB"+label+"_"+self.channel+"_"+self.wtagger_label,"rrv_alpha_CB"+label+"_"+self.channel+"_"+self.wtagger_label,-1,-2,-0.5);
                rrv_n_CB=RooRealVar("rrv_n_CB"+label+"_"+self.channel+"_"+self.wtagger_label,"rrv_n_CB"+label+"_"+self.channel+"_"+self.wtagger_label,20.,10,80 );
            elif label_tstring.Contains("H700"):
                rrv_mean_CB=RooRealVar("rrv_mean_CB"+label+"_"+self.channel+"_"+self.wtagger_label,"rrv_mean_CB"+label+"_"+self.channel+"_"+self.wtagger_label,700,650,750);
                rrv_sigma_CB=RooRealVar("rrv_sigma_CB"+label+"_"+self.channel+"_"+self.wtagger_label,"rrv_sigma_CB"+label+"_"+self.channel+"_"+self.wtagger_label,100,40,150);
                rrv_alpha_CB=RooRealVar("rrv_alpha_CB"+label+"_"+self.channel+"_"+self.wtagger_label,"rrv_alpha_CB"+label+"_"+self.channel+"_"+self.wtagger_label,-1,-3,-0.1);
                rrv_n_CB=RooRealVar("rrv_n_CB"+label+"_"+self.channel+"_"+self.wtagger_label,"rrv_n_CB"+label+"_"+self.channel+"_"+self.wtagger_label,20.,10,40);
            elif label_tstring.Contains("ggH800"): 
                rrv_mean_CB=RooRealVar("rrv_mean_CB"+label+"_"+self.channel+"_"+self.wtagger_label,"rrv_mean_CB"+label+"_"+self.channel+"_"+self.wtagger_label,780,700,850);
                rrv_sigma_CB=RooRealVar("rrv_sigma_CB"+label+"_"+self.channel+"_"+self.wtagger_label,"rrv_sigma_CB"+label+"_"+self.channel+"_"+self.wtagger_label,140,120,160);
                rrv_alpha_CB=RooRealVar("rrv_alpha_CB"+label+"_"+self.channel+"_"+self.wtagger_label,"rrv_alpha_CB"+label+"_"+self.channel+"_"+self.wtagger_label,-1,-4,0);
                rrv_n_CB=RooRealVar("rrv_n_CB"+label+"_"+self.channel+"_"+self.wtagger_label,"rrv_n_CB"+label+"_"+self.channel+"_"+self.wtagger_label,5  , 2, 7);
            elif label_tstring.Contains("vbfH800"): 
                rrv_mean_CB=RooRealVar("rrv_mean_CB"+label+"_"+self.channel,"rrv_mean_CB"+label+"_"+self.channel,800,750,850);
                rrv_sigma_CB=RooRealVar("rrv_sigma_CB"+label+"_"+self.channel,"rrv_sigma_CB"+label+"_"+self.channel,140,120,160);
                rrv_alpha_CB=RooRealVar("rrv_alpha_CB"+label+"_"+self.channel,"rrv_alpha_CB"+label+"_"+self.channel,-1,-4,0);
                rrv_n_CB=RooRealVar("rrv_n_CB"+label+"_"+self.channel,"rrv_n_CB"+label+"_"+self.channel,5  , 2, 7);
            elif label_tstring.Contains("ggH900"):
                rrv_mean_CB=RooRealVar("rrv_mean_CB"+label+"_"+self.channel,"rrv_mean_CB"+label+"_"+self.channel,880,820,950);
                rrv_sigma_CB=RooRealVar("rrv_sigma_CB"+label+"_"+self.channel,"rrv_sigma_CB"+label+"_"+self.channel,170,140,200);
                rrv_alpha_CB=RooRealVar("rrv_alpha_CB"+label+"_"+self.channel,"rrv_alpha_CB"+label+"_"+self.channel,1,0,4);
                rrv_n_CB=RooRealVar("rrv_n_CB"+label+"_"+self.channel,"rrv_n_CB"+label+"_"+self.channel, 2., 0.5,5);
            elif label_tstring.Contains("vbfH900"):
                rrv_mean_CB=RooRealVar("rrv_mean_CB"+label+"_"+self.channel,"rrv_mean_CB"+label+"_"+self.channel,900,880,920);
                rrv_sigma_CB=RooRealVar("rrv_sigma_CB"+label+"_"+self.channel,"rrv_sigma_CB"+label+"_"+self.channel,170,140,200);
                rrv_alpha_CB=RooRealVar("rrv_alpha_CB"+label+"_"+self.channel,"rrv_alpha_CB"+label+"_"+self.channel,1);
                rrv_n_CB=RooRealVar("rrv_n_CB"+label+"_"+self.channel,"rrv_n_CB"+label+"_"+self.channel, 2., 0.5,5);
            elif label_tstring.Contains("ggH1000"): 
                rrv_mean_CB=RooRealVar("rrv_mean_CB"+label+"_"+self.channel,"rrv_mean_CB"+label+"_"+self.channel,920,800,1150);
                rrv_sigma_CB=RooRealVar("rrv_sigma_CB"+label+"_"+self.channel,"rrv_sigma_CB"+label+"_"+self.channel,200,100,300);
                rrv_alpha_CB=RooRealVar("rrv_alpha_CB"+label+"_"+self.channel,"rrv_alpha_CB"+label+"_"+self.channel,1,0.1,3);
                rrv_n_CB=RooRealVar("rrv_n_CB"+label+"_"+self.channel,"rrv_n_CB"+label+"_"+self.channel,2.,0.5,4);
            elif label_tstring.Contains("vbfH1000"): 
                rrv_mean_CB=RooRealVar("rrv_mean_CB"+label+"_"+self.channel,"rrv_mean_CB"+label+"_"+self.channel,1000,980,1150);
                rrv_sigma_CB=RooRealVar("rrv_sigma_CB"+label+"_"+self.channel,"rrv_sigma_CB"+label+"_"+self.channel,200,100,300);
                rrv_alpha_CB=RooRealVar("rrv_alpha_CB"+label+"_"+self.channel,"rrv_alpha_CB"+label+"_"+self.channel,0.72);
                rrv_n_CB=RooRealVar("rrv_n_CB"+label+"_"+self.channel,"rrv_n_CB"+label+"_"+self.channel,2.,0.5,4);
            else:
                if label_tstring.Contains("600") and (not  label_tstring.Contains("1600") ):
                    rrv_mean_CB=RooRealVar("rrv_mean_CB"+label+"_"+self.channel+"_"+self.wtagger_label,"rrv_mean_CB"+label+"_"+self.channel+"_"+self.wtagger_label, 600, 550, 650);
                    rrv_sigma_CB=RooRealVar("rrv_sigma_CB"+label+"_"+self.channel+"_"+self.wtagger_label,"rrv_sigma_CB"+label+"_"+self.channel+"_"+self.wtagger_label, 30,10 ,80);

                elif label_tstring.Contains("700") and (not  label_tstring.Contains("1700") ):
                     rrv_mean_CB=RooRealVar("rrv_mean_CB"+label+"_"+self.channel+"_"+self.wtagger_label,"rrv_mean_CB"+label+"_"+self.channel+"_"+self.wtagger_label, 700, 600, 800);
                     rrv_sigma_CB=RooRealVar("rrv_sigma_CB"+label+"_"+self.channel+"_"+self.wtagger_label,"rrv_sigma_CB"+label+"_"+self.channel+"_"+self.wtagger_label, 30,10 ,80);
                     
                elif label_tstring.Contains("800") and (not  label_tstring.Contains("1800") ):
                     rrv_mean_CB=RooRealVar("rrv_mean_CB"+label+"_"+self.channel+"_"+self.wtagger_label,"rrv_mean_CB"+label+"_"+self.channel+"_"+self.wtagger_label, 800, 600, 800);
                     rrv_sigma_CB=RooRealVar("rrv_sigma_CB"+label+"_"+self.channel+"_"+self.wtagger_label,"rrv_sigma_CB"+label+"_"+self.channel+"_"+self.wtagger_label, 40,10 ,90);
                     
                elif label_tstring.Contains("900") and (not  label_tstring.Contains("1900") ):
                    rrv_mean_CB=RooRealVaDr("rrv_mean_CB"+label+"_"+self.channel+"_"+self.wtagger_label,"rrv_mean_CB"+label+"_"+self.channel+"_"+self.wtagger_label, 900, 600, 800);
                    rrv_sigma_CB=RooRealVar("rrv_sigma_CB"+label+"_"+self.channel+"_"+self.wtagger_label,"rrv_sigma_CB"+label+"_"+self.channel+"_"+self.wtagger_label, 40,10 ,90);

                elif label_tstring.Contains("1000"):
                    rrv_mean_CB=RooRealVar("rrv_mean_CB"+label+"_"+self.channel+"_"+self.wtagger_label,"rrv_mean_CB"+label+"_"+self.channel+"_"+self.wtagger_label,1000, 900,1100);
                    rrv_sigma_CB=RooRealVar("rrv_sigma_CB"+label+"_"+self.channel+"_"+self.wtagger_label,"rrv_sigma_CB"+label+"_"+self.channel+"_"+self.wtagger_label, 50,20 ,120);

                elif label_tstring.Contains("1100"):
                    rrv_mean_CB=RooRealVar("rrv_mean_CB"+label+"_"+self.channel+"_"+self.wtagger_label,"rrv_mean_CB"+label+"_"+self.channel+"_"+self.wtagger_label,1100,1000,1200);
                    rrv_sigma_CB=RooRealVar("rrv_sigma_CB"+label+"_"+self.channel+"_"+self.wtagger_label,"rrv_sigma_CB"+label+"_"+self.channel+"_"+self.wtagger_label, 50,20 ,120);

                elif label_tstring.Contains("1200"):
                    rrv_mean_CB=RooRealVar("rrv_mean_CB"+label+"_"+self.channel+"_"+self.wtagger_label,"rrv_mean_CB"+label+"_"+self.channel+"_"+self.wtagger_label,1200,1100,1300);
                    rrv_sigma_CB=RooRealVar("rrv_sigma_CB"+label+"_"+self.channel+"_"+self.wtagger_label,"rrv_sigma_CB"+label+"_"+self.channel+"_"+self.wtagger_label, 50,20 ,120);

                elif label_tstring.Contains("1300"):
                    rrv_mean_CB=RooRealVar("rrv_mean_CB"+label+"_"+self.channel+"_"+self.wtagger_label,"rrv_mean_CB"+label+"_"+self.channel+"_"+self.wtagger_label,1300,1200,1400);
                    rrv_sigma_CB=RooRealVar("rrv_sigma_CB"+label+"_"+self.channel+"_"+self.wtagger_label,"rrv_sigma_CB"+label+"_"+self.channel+"_"+self.wtagger_label, 50,20 ,120);

                elif label_tstring.Contains("1400"):
                    rrv_mean_CB=RooRealVar("rrv_mean_CB"+label+"_"+self.channel+"_"+self.wtagger_label,"rrv_mean_CB"+label+"_"+self.channel+"_"+self.wtagger_label,1400,1300,1500);
                    rrv_sigma_CB=RooRealVar("rrv_sigma_CB"+label+"_"+self.channel+"_"+self.wtagger_label,"rrv_sigma_CB"+label+"_"+self.channel+"_"+self.wtagger_label, 50,20 ,120);

                elif label_tstring.Contains("1500"):
                    rrv_mean_CB=RooRealVar("rrv_mean_CB"+label+"_"+self.channel+"_"+self.wtagger_label,"rrv_mean_CB"+label+"_"+self.channel+"_"+self.wtagger_label,1500,1400,1600);
                    rrv_sigma_CB=RooRealVar("rrv_sigma_CB"+label+"_"+self.channel+"_"+self.wtagger_label,"rrv_sigma_CB"+label+"_"+self.channel+"_"+self.wtagger_label, 50,20 ,120);
                    
                elif label_tstring.Contains("1600"):
                    rrv_mean_CB=RooRealVar("rrv_mean_CB"+label+"_"+self.channel+"_"+self.wtagger_label,"rrv_mean_CB"+label+"_"+self.channel+"_"+self.wtagger_label,1600,1500,1700);
                    rrv_sigma_CB=RooRealVar("rrv_sigma_CB"+label+"_"+self.channel+"_"+self.wtagger_label,"rrv_sigma_CB"+label+"_"+self.channel+"_"+self.wtagger_label, 50,20 ,120);

                elif label_tstring.Contains("1700"):
                    rrv_sigma_CB=RooRealVar("rrv_sigma_CB"+label+"_"+self.channel+"_"+self.wtagger_label,"rrv_sigma_CB"+label+"_"+self.channel+"_"+self.wtagger_label, 50,20 ,120);
                    rrv_mean_CB=RooRealVar("rrv_mean_CB"+label+"_"+self.channel+"_"+self.wtagger_label,"rrv_mean_CB"+label+"_"+self.channel+"_"+self.wtagger_label,1700,1500,1800);

                elif label_tstring.Contains("1800"):
                    rrv_mean_CB=RooRealVar("rrv_mean_CB"+label+"_"+self.channel+"_"+self.wtagger_label,"rrv_mean_CB"+label+"_"+self.channel+"_"+self.wtagger_label,1800,1500,1900);
                    rrv_sigma_CB=RooRealVar("rrv_sigma_CB"+label+"_"+self.channel+"_"+self.wtagger_label,"rrv_sigma_CB"+label+"_"+self.channel+"_"+self.wtagger_label, 50,20 ,120);

                elif label_tstring.Contains("1900"):
                    rrv_mean_CB=RooRealVar("rrv_mean_CB"+label+"_"+self.channel+"_"+self.wtagger_label,"rrv_mean_CB"+label+"_"+self.channel+"_"+self.wtagger_label,1900,1500,2000);
                    rrv_sigma_CB=RooRealVar("rrv_sigma_CB"+label+"_"+self.channel+"_"+self.wtagger_label,"rrv_sigma_CB"+label+"_"+self.channel+"_"+self.wtagger_label, 50,20 ,120);

                elif label_tstring.Contains("2000"):
                    rrv_mean_CB=RooRealVar("rrv_mean_CB"+label+"_"+self.channel+"_"+self.wtagger_label,"rrv_mean_CB"+label+"_"+self.channel+"_"+self.wtagger_label,2000,1800,2200);
                    rrv_sigma_CB=RooRealVar("rrv_sigma_CB"+label+"_"+self.channel+"_"+self.wtagger_label,"rrv_sigma_CB"+label+"_"+self.channel+"_"+self.wtagger_label, 50,20 ,120);

                elif label_tstring.Contains("2100"):
                    rrv_mean_CB=RooRealVar("rrv_mean_CB"+label+"_"+self.channel+"_"+self.wtagger_label,"rrv_mean_CB"+label+"_"+self.channel+"_"+self.wtagger_label,2100,1800,2300);
                    rrv_sigma_CB=RooRealVar("rrv_sigma_CB"+label+"_"+self.channel+"_"+self.wtagger_label,"rrv_sigma_CB"+label+"_"+self.channel+"_"+self.wtagger_label, 50,20 ,120);

                elif label_tstring.Contains("2200"):
                    rrv_mean_CB=RooRealVar("rrv_mean_CB"+label+"_"+self.channel+"_"+self.wtagger_label,"rrv_mean_CB"+label+"_"+self.channel+"_"+self.wtagger_label,2200,1800,2400);
                    rrv_sigma_CB=RooRealVar("rrv_sigma_CB"+label+"_"+self.channel+"_"+self.wtagger_label,"rrv_sigma_CB"+label+"_"+self.channel+"_"+self.wtagger_label, 50,20 ,120);

                elif label_tstring.Contains("2300"):
                    rrv_mean_CB=RooRealVar("rrv_mean_CB"+label+"_"+self.channel+"_"+self.wtagger_label,"rrv_mean_CB"+label+"_"+self.channel+"_"+self.wtagger_label,2300,1800,2500);
                    rrv_sigma_CB=RooRealVar("rrv_sigma_CB"+label+"_"+self.channel+"_"+self.wtagger_label,"rrv_sigma_CB"+label+"_"+self.channel+"_"+self.wtagger_label, 50,20 ,120);

                elif label_tstring.Contains("2400"):
                    rrv_mean_CB=RooRealVar("rrv_mean_CB"+label+"_"+self.channel+"_"+self.wtagger_label,"rrv_mean_CB"+label+"_"+self.channel+"_"+self.wtagger_label,2400,1800,2600);
                    rrv_sigma_CB=RooRealVar("rrv_sigma_CB"+label+"_"+self.channel+"_"+self.wtagger_label,"rrv_sigma_CB"+label+"_"+self.channel+"_"+self.wtagger_label, 50,20 ,120);

                elif label_tstring.Contains("2500"):
                    rrv_mean_CB=RooRealVar("rrv_mean_CB"+label+"_"+self.channel+"_"+self.wtagger_label,"rrv_mean_CB"+label+"_"+self.channel+"_"+self.wtagger_label,2500,2000,2700);
                    rrv_sigma_CB=RooRealVar("rrv_sigma_CB"+label+"_"+self.channel+"_"+self.wtagger_label,"rrv_sigma_CB"+label+"_"+self.channel+"_"+self.wtagger_label, 50,20 ,120);
                else :
                    rrv_mean_CB=RooRealVar("rrv_mean_CB"+label+"_"+self.channel+"_"+self.wtagger_label,"rrv_mean_CB"+label+"_"+self.channel+"_"+self.wtagger_label,700,550,2500);
                    rrv_sigma_CB=RooRealVar("rrv_sigma_CB"+label+"_"+self.channel+"_"+self.wtagger_label,"rrv_sigma_CB"+label+"_"+self.channel+"_"+self.wtagger_label, 50,20 ,120);

                rrv_alpha_CB=RooRealVar("rrv_alpha_CB"+label+"_"+self.channel+"_"+self.wtagger_label,"rrv_alpha_CB"+label+"_"+self.channel+"_"+self.wtagger_label,4,1,5);
                rrv_n_CB=RooRealVar("rrv_n_CB"+label+"_"+self.channel+"_"+self.wtagger_label,"rrv_n_CB"+label+"_"+self.channel+"_"+self.wtagger_label,20.,10,40);

            model_pdf = RooCBShape("model_pdf"+label+"_"+self.channel+mass_spectrum,"model_pdf"+label+"_"+self.channel+mass_spectrum, rrv_x,rrv_mean_CB,rrv_sigma_CB,rrv_alpha_CB,rrv_n_CB);

        if in_model_name == "ArgusBW_v1":
            label_tstring=TString(label);
            if label_tstring.Contains("ggH1000"): 
                rrv_width_BW=RooRealVar("rrv_width_BW"+label+"_"+self.channel,"rrv_width_BW"+label+"_"+self.channel,100,50,600);
                rrv_m0_Argus=RooRealVar("rrv_m0_Argus"+label+"_"+self.channel,"rrv_m0_Argus"+label+"_"+self.channel, 950         );
                rrv_c_Argus=RooRealVar("rrv_c_Argus"+label+"_"+self.channel,"rrv_c_Argus"+label+"_"+self.channel,-1,-2,-1e-1);
                rrv_frac=RooRealVar("rrv_frac"+label+"_"+self.channel,"rrv_frac"+label+"_"+self.channel,0.5,0.0,1.);
            else:
                rrv_width_BW=RooRealVar("rrv_width_BW"+label+"_"+self.channel,"rrv_width_BW"+label+"_"+self.channel,200,50,400);
                rrv_m0_Argus=RooRealVar("rrv_m0_Argus"+label+"_"+self.channel,"rrv_m0_Argus"+label+"_"+self.channel,1000);
                rrv_c_Argus=RooRealVar("rrv_c_Argus"+label+"_"+self.channel,"rrv_c_Argus"+label+"_"+self.channel,-1,-2,0.1);
                rrv_frac=RooRealVar("rrv_frac"+label+"_"+self.channel,"rrv_frac"+label+"_"+self.channel,0.5,0.0,1.);
            bw = RooBreitWigner("bw"+label+"_"+self.channel,"bw"+label+"_"+self.channel, rrv_x,rrv_m0_Argus,rrv_width_BW);
            argus=RooArgusBG("argus"+label+"_"+self.channel,"argus"+label+"_"+self.channel, rrv_x, rrv_m0_Argus,rrv_c_Argus);
            model_pdf = RooAddPdf("model_pdf"+label+"_"+self.channel+mass_spectrum,"model_pdf"+label+"_"+self.channel+mass_spectrum, RooArgList(bw,argus), RooArgList(rrv_frac));
    
        if in_model_name == "CBBW": # FFT: BreitWigner*CBShape
            rrv_mean_CB=RooRealVar("rrv_mean_CB"+label+"_"+self.channel,"rrv_mean_CB"+label+"_"+self.channel,84.0,78,88);
            rrv_sigma_CB=RooRealVar("rrv_sigma_CB"+label+"_"+self.channel,"rrv_sigma_CB"+label+"_"+self.channel,7,4,10);
            rrv_alpha_CB=RooRealVar("rrv_alpha_CB"+label+"_"+self.channel,"rrv_alpha_CB"+label+"_"+self.channel,-2,-4,-1);
            rrv_n_CB=RooRealVar("rrv_n_CB"+label+"_"+self.channel,"rrv_n_CB"+label+"_"+self.channel,0.5,0.,2);
            rrv_mean_BW=RooRealVar("rrv_mean_BW"+label+"_"+self.channel,"rrv_mean_BW"+label+"_"+self.channel,0);
            rrv_width_BW=RooRealVar("rrv_width_BW"+label+"_"+self.channel,"rrv_width_BW"+label+"_"+self.channel,10,5,20);
            cbshape = RooCBShape("cbshape"+label+"_"+self.channel,"cbshape"+label+"_"+self.channel, rrv_x,rrv_mean_CB,rrv_sigma_CB,rrv_alpha_CB,rrv_n_CB);
            bw = RooBreitWigner("bw"+label+"_"+self.channel,"bw"+label+"_"+self.channel, rrv_x,rrv_mean_BW,rrv_width_BW);
            model_pdf = RooFFTConvPdf("model_pdf"+label+"_"+self.channel+mass_spectrum,"model_pdf"+label+"_"+self.channel+mass_spectrum, rrv_x, cbshape, bw);

        if in_model_name == "LDGaus": # FFT: Landau*Gaus
            rrv_mean_landau=RooRealVar("rrv_mean_landau"+label+"_"+self.channel,"rrv_mean_landau"+label+"_"+self.channel,84.0,78,88);
            rrv_sigma_landau=RooRealVar("rrv_sigma_landau"+label+"_"+self.channel,"rrv_sigma_landau"+label+"_"+self.channel,7,4,10);
            rrv_mean_gaus=RooRealVar("rrv_mean_gaus"+label+"_"+self.channel,"rrv_mean_gaus"+label+"_"+self.channel,0);
            rrv_sigma_gaus=RooRealVar("rrv_sigma_gaus"+label+"_"+self.channel,"rrv_sigma_gaus"+label+"_"+self.channel,16,10,20);
            landau = RooLandau("landau"+label+"_"+self.channel,"landau"+label+"_"+self.channel, rrv_x,rrv_mean_landau,rrv_sigma_landau);
            gaus = RooBreitWigner("gaus"+label+"_"+self.channel,"gaus"+label+"_"+self.channel, rrv_x,rrv_mean_gaus,rrv_sigma_gaus);
            model_pdf = RooFFTConvPdf("model_pdf"+label+"_"+self.channel+mass_spectrum,"model_pdf"+label+"_"+self.channel+mass_spectrum, rrv_x, landau, gaus);

        if in_model_name == "ExpN":
           rrv_c_ExpN = RooRealVar("rrv_c_ExpN"+label+"_"+self.channel,"rrv_c_ExpN"+label+"_"+self.channel,-3e-3,-1e-1,-1e-5);
           if(ismc==1):
            rrv_n_ExpN = RooRealVar("rrv_n_ExpN"+label+"_"+self.channel,"rrv_n_ExpN"+label+"_"+self.channel, 1e3, -1e2, 1e4);
           else :
            if self.channel == "el" :
             rrv_n_ExpN = RooRealVar("rrv_n_ExpN"+label+"_"+self.channel,"rrv_n_ExpN"+label+"_"+self.channel, 1e3, -1e2, 1e4);
            elif self.wtagger_label == "LP" :
             rrv_n_ExpN = RooRealVar("rrv_n_ExpN"+label+"_"+self.channel,"rrv_n_ExpN"+label+"_"+self.channel, 1e3, -1e2, 1e4);
            else:
             rrv_n_ExpN = RooRealVar("rrv_n_ExpN"+label+"_"+self.channel,"rrv_n_ExpN"+label+"_"+self.channel, 1e2, -1e2, 7e3);

           model_pdf = ROOT.RooExpNPdf("model_pdf"+label+"_"+self.channel+mass_spectrum,"model_pdf"+label+"_"+self.channel+mass_spectrum,rrv_x,rrv_c_ExpN,rrv_n_ExpN);
                                                                                                                             

        if in_model_name == "ExpTail":
            rrv_s_ExpTail = RooRealVar("rrv_s_ExpTail"+label+"_"+self.channel,"rrv_s_ExpTail"+label+"_"+self.channel, 170,50,300);
            rrv_a_ExpTail = RooRealVar("rrv_a_ExpTail"+label+"_"+self.channel,"rrv_a_ExpTail"+label+"_"+self.channel, 3e-3,0,1e3);
            model_pdf = ROOT.RooExpTailPdf("model_pdf"+label+"_"+self.channel+mass_spectrum,"model_pdf"+label+"_"+self.channel+mass_spectrum,rrv_x,rrv_s_ExpTail, rrv_a_ExpTail);

        if in_model_name == "2Exp":
            rrv_c0_2Exp = RooRealVar("rrv_c0_2Exp"+label+"_"+self.channel,"rrv_c0_2Exp"+label+"_"+self.channel, -5e-3, -8e-3,-4e-3);
            rrv_c1_2Exp = RooRealVar("rrv_c1_2Exp"+label+"_"+self.channel,"rrv_c1_2Exp"+label+"_"+self.channel, -1e-3, -4e-3,-1e-4);
            rrv_frac_2Exp = RooRealVar("rrv_frac_2Exp"+label+"_"+self.channel,"rrv_frac_2Exp"+label+"_"+self.channel, 0., 0., 1e-2);
            model_pdf = ROOT.Roo2ExpPdf("model_pdf"+label+"_"+self.channel+mass_spectrum,"model_pdf"+label+"_"+self.channel+mass_spectrum,rrv_x,rrv_c0_2Exp,rrv_c1_2Exp,rrv_frac_2Exp);

        if in_model_name == "Exp"  or in_model_name == "Exp_sr":
            rrv_c_Exp = RooRealVar("rrv_c_Exp"+label+"_"+self.channel,"rrv_c_Exp"+label+"_"+self.channel,-0.05,-0.1,0.);
            model_pdf = ROOT.RooExponential("model_pdf"+label+"_"+self.channel+mass_spectrum,"model_pdf"+label+"_"+self.channel+mass_spectrum,rrv_x,rrv_c_Exp);

        if in_model_name == "ErfExp" :
            rrv_c_ErfExp = RooRealVar("rrv_c_ErfExp"+label+"_"+self.channel,"rrv_c_ErfExp"+label+"_"+self.channel,-0.05,-0.1,-1e-4);
            rrv_offset_ErfExp = RooRealVar("rrv_offset_ErfExp"+label+"_"+self.channel,"rrv_offset_ErfExp"+label+"_"+self.channel,60.,30.,120);
            rrv_width_ErfExp = RooRealVar("rrv_width_ErfExp"+label+"_"+self.channel,"rrv_width_ErfExp"+label+"_"+self.channel,30.)#,10, 60.);
            model_pdf = ROOT.RooErfExpPdf("model_pdf"+label+"_"+self.channel+mass_spectrum,"model_pdf"+label+"_"+self.channel+mass_spectrum,rrv_x,rrv_c_ErfExp,rrv_offset_ErfExp,rrv_width_ErfExp);


        if in_model_name == "ErfExp_v1" : #different init-value and range
            rrv_c_ErfExp = RooRealVar("rrv_c_ErfExp"+label+"_"+self.channel,"rrv_c_ErfExp"+label+"_"+self.channel,-0.006,-0.1,0.);
            rrv_offset_ErfExp = RooRealVar("rrv_offset_ErfExp"+label+"_"+self.channel,"rrv_offset_ErfExp"+label+"_"+self.channel,450.,400.,550.);
            rrv_width_ErfExp = RooRealVar("rrv_width_ErfExp"+label+"_"+self.channel,"rrv_width_ErfExp"+label+"_"+self.channel,70.,10,100.);
            model_pdf = ROOT.RooErfExpPdf("model_pdf"+label+"_"+self.channel+mass_spectrum,"model_pdf"+label+"_"+self.channel+mass_spectrum,rrv_x,rrv_c_ErfExp,rrv_offset_ErfExp,rrv_width_ErfExp);
            #model_pdf = RooGenericPdf("model_pdf"+label+"_"+self.channel+mass_spectrum,"model_pdf"+label+"_"+self.channel+mass_spectrum, "TMath::Exp(%s*%s)*(1.+TMath::Erf((%s-%s)/%s))/2."%(rrv_c_ErfExp.GetName(),rrv_x.GetName(), rrv_x.GetName(),rrv_offset_ErfExp.GetName(), rrv_width_ErfExp.GetName()), RooArgList(rrv_x,rrv_c_ErfExp,rrv_offset_ErfExp,rrv_width_ErfExp) )

        if in_model_name == "ErfExp_v2" : #different init-value and range
            rrv_c_ErfExp = RooRealVar("rrv_c_ErfExp"+label+"_"+self.channel,"rrv_c_ErfExp"+label+"_"+self.channel,-0.005,-0.1,0.);
            rrv_offset_ErfExp = RooRealVar("rrv_offset_ErfExp"+label+"_"+self.channel,"rrv_offset_ErfExp"+label+"_"+self.channel,450.,400.,500.);
            rrv_width_ErfExp = RooRealVar("rrv_width_ErfExp"+label+"_"+self.channel,"rrv_width_ErfExp"+label+"_"+self.channel, 50.,10,100.);
            rrv_residue_ErfExp = RooRealVar("rrv_residue_ErfExp"+label+"_"+self.channel,"rrv_residue_ErfExp"+label+"_"+self.channel,0.,0.,1.);
            #model_pdf = ROOT.RooErfExpPdf("model_pdf"+label+"_"+self.channel+mass_spectrum,"model_pdf"+label+"_"+self.channel+mass_spectrum,rrv_x,rrv_c_ErfExp,rrv_offset_ErfExp,rrv_width_ErfExp);
            model_pdf = RooGenericPdf("model_pdf"+label+"_"+self.channel+mass_spectrum,"model_pdf"+label+"_"+self.channel+mass_spectrum, "(TMath::Exp(%s*%s) + %s)*(1.+TMath::Erf((%s-%s)/%s))/2. "%(rrv_c_ErfExp.GetName(),rrv_x.GetName(), rrv_residue_ErfExp.GetName(), rrv_x.GetName(),rrv_offset_ErfExp.GetName(), rrv_width_ErfExp.GetName()), RooArgList(rrv_x,rrv_c_ErfExp,rrv_offset_ErfExp,rrv_width_ErfExp,rrv_residue_ErfExp) )

        if in_model_name == "ErfExp_v3" : #different init-value and range
            rrv_c_ErfExp = RooRealVar("rrv_c_ErfExp"+label+"_"+self.channel,"rrv_c_ErfExp"+label+"_"+self.channel,-0.005,-0.1,0.);
            rrv_offset_ErfExp = RooRealVar("rrv_offset_ErfExp"+label+"_"+self.channel,"rrv_offset_ErfExp"+label+"_"+self.channel,450.,400,500.);
            rrv_width_ErfExp = RooRealVar("rrv_width_ErfExp"+label+"_"+self.channel,"rrv_width_ErfExp"+label+"_"+self.channel, 50.,10,100.);
            rrv_residue_ErfExp = RooRealVar("rrv_residue_ErfExp"+label+"_"+self.channel,"rrv_residue_ErfExp"+label+"_"+self.channel,0.,0.,1.);
            rrv_high_ErfExp = RooRealVar("rrv_high_ErfExp"+label+"_"+self.channel,"rrv_high_ErfExp"+label+"_"+self.channel,1.,0.,400);
            rrv_high_ErfExp.setConstant(kTRUE);
            model_pdf = RooGenericPdf("model_pdf"+label+"_"+self.channel+mass_spectrum,"model_pdf"+label+"_"+self.channel+mass_spectrum, "(TMath::Exp(%s*%s) + %s)* TMath::Power( ((1+TMath::Erf((%s-%s)/%s))/2.), %s )"%(rrv_c_ErfExp.GetName(),rrv_x.GetName(), rrv_residue_ErfExp.GetName(),rrv_x.GetName(),rrv_offset_ErfExp.GetName(), rrv_width_ErfExp.GetName(), rrv_high_ErfExp.GetName()), RooArgList(rrv_x,rrv_c_ErfExp,rrv_offset_ErfExp,rrv_high_ErfExp,rrv_width_ErfExp,rrv_residue_ErfExp) )
      
            
        if in_model_name == "ErfExpGaus":
            rrv_c_ErfExp = RooRealVar("rrv_c_ErfExp"+label+"_"+self.channel,"rrv_c_ErfExp"+label+"_"+self.channel,-0.05,-0.4,0.);
            rrv_offset_ErfExp = RooRealVar("rrv_offset_ErfExp"+label+"_"+self.channel,"rrv_offset_ErfExp"+label+"_"+self.channel,100.,10.,300.);
            rrv_width_ErfExp = RooRealVar("rrv_width_ErfExp"+label+"_"+self.channel,"rrv_width_ErfExp"+label+"_"+self.channel,30.,10,100.);
            rrv_mean_gaus=RooRealVar("rrv_mean_gaus"+label+"_"+self.channel,"rrv_mean_gaus"+label+"_"+self.channel,82,78,87);
            rrv_sigma_gaus=RooRealVar("rrv_sigma_gaus"+label+"_"+self.channel,"rrv_sigma_gaus"+label+"_"+self.channel,7,4,10);
            rrv_high = RooRealVar("rrv_high"+label+"_"+self.channel,"rrv_high"+label+"_"+self.channel,0.7,0.,1.);

            erfExp = ROOT.RooErfExpPdf("erfExp"+label+"_"+self.channel,"erfExp"+label+"_"+self.channel,rrv_x,rrv_c_ErfExp,rrv_offset_ErfExp,rrv_width_ErfExp);
            gaus = RooGaussian("gaus"+label+"_"+self.channel,"gaus"+label+"_"+self.channel, rrv_x,rrv_mean_gaus,rrv_sigma_gaus);

            model_pdf =RooAddPdf("model_pdf"+label+"_"+self.channel+mass_spectrum,"model_pdf"+label+"_"+self.channel+mass_spectrum,RooArgList(erfExp,gaus),RooArgList(rrv_high))

        if in_model_name == "ErfExpGaus_sp":#offset == mean
            rrv_c_ErfExp = RooRealVar("rrv_c_ErfExp"+label+"_"+self.channel,"rrv_c_ErfExp"+label+"_"+self.channel,-0.05,-0.2,0.);
            rrv_width_ErfExp = RooRealVar("rrv_width_ErfExp"+label+"_"+self.channel,"rrv_width_ErfExp"+label+"_"+self.channel,30.,10,200.);
            rrv_mean1_gaus=RooRealVar("rrv_mean1_gaus"+label+"_"+self.channel,"rrv_mean1_gaus"+label+"_"+self.channel,84,78,88);
            rrv_sigma1_gaus=RooRealVar("rrv_sigma1_gaus"+label+"_"+self.channel,"rrv_sigma1_gaus"+label+"_"+self.channel,7,4,10);
            rrv_high = RooRealVar("rrv_high"+label+"_"+self.channel,"rrv_high"+label+"_"+self.channel,0.5,0.,1.);
            erfExp = ROOT.RooErfExpPdf("erfExp"+label+"_"+self.channel,"erfExp"+label+"_"+self.channel,rrv_x,rrv_c_ErfExp,rrv_mean1_gaus,rrv_width_ErfExp);
            gaus = RooGaussian("gaus"+label+"_"+self.channel,"gaus"+label+"_"+self.channel, rrv_x,rrv_mean1_gaus,rrv_sigma1_gaus);
            model_pdf =RooAddPdf("model_pdf"+label+"_"+self.channel+mass_spectrum,"model_pdf"+label+"_"+self.channel+mass_spectrum,RooArgList(erfExp,gaus),RooArgList(rrv_high))

        if in_model_name == "ExpGaus":
            rrv_c_Exp = RooRealVar("rrv_c_Exp"+label+"_"+self.channel,"rrv_c_Exp"+label+"_"+self.channel,0.05,-0.2,0.2);
            rrv_mean1_gaus=RooRealVar("rrv_mean1_gaus"+label+"_"+self.channel,"rrv_mean1_gaus"+label+"_"+self.channel,84,78,88);
            rrv_sigma1_gaus=RooRealVar("rrv_smgma1_gaus"+label+"_"+self.channel,"rrv_sigma1_gaus"+label+"_"+self.channel,7,4,10);
            rrv_high = RooRealVar("rrv_high"+label+"_"+self.channel,"rrv_high"+label+"_"+self.channel,0.5,0.,1.);
            exp = ROOT.RooExponential("exp"+label+"_"+self.channel,"exp"+label+"_"+self.channel,rrv_x,rrv_c_Exp);
            gaus = RooGaussian("gaus"+label+"_"+self.channel,"gaus"+label+"_"+self.channel, rrv_x,rrv_mean1_gaus,rrv_sigma1_gaus);
            model_pdf =RooAddPdf("model_pdf"+label+"_"+self.channel+mass_spectrum,"model_pdf"+label+"_"+self.channel+mass_spectrum,RooArgList(exp,gaus),RooArgList(rrv_high))

        if in_model_name == "ErfExpGaus_v0":
            rrv_c_ErfExp = RooRealVar("rrv_c_ErfExp"+label+"_"+self.channel,"rrv_c_ErfExp"+label+"_"+self.channel,-0.05,-0.2,0.);
            rrv_offset_ErfExp = RooRealVar("rrv_offset_ErfExp"+label+"_"+self.channel,"rrv_offset_ErfExp"+label+"_"+self.channel,100.,10.,140.);
            rrv_width_ErfExp = RooRealVar("rrv_width_ErfExp"+label+"_"+self.channel,"rrv_width_ErfExp"+label+"_"+self.channel,30.,10,100.);
            rrv_mean_gaus=RooRealVar("rrv_mean_gaus"+label+"_"+self.channel,"rrv_mean_gaus"+label+"_"+self.channel,84,78,88);
            rrv_sigma_gaus=RooRealVar("rrv_sigma_gaus"+label+"_"+self.channel,"rrv_sigma_gaus"+label+"_"+self.channel,7,4,10);
            rrv_high = RooRealVar("rrv_high"+label+"_"+self.channel,"rrv_high"+label+"_"+self.channel,0.7,0.,1.);
            erfExp = ROOT.RooErfExpPdf("erfExp"+label+"_"+self.channel,"erfExp"+label+"_"+self.channel,rrv_x,rrv_c_ErfExp,rrv_offset_ErfExp,rrv_width_ErfExp);
            gaus = RooGaussian("gaus"+label+"_"+self.channel,"gaus"+label+"_"+self.channel, rrv_x,rrv_mean_gaus,rrv_sigma_gaus);
            model_pdf =RooAddPdf("model_pdf"+label+"_"+self.channel+mass_spectrum,"model_pdf"+label+"_"+self.channel+mass_spectrum,RooArgList(erfExp,gaus),RooArgList(rrv_high))
    
        if in_model_name == "ErfExpGaus_v1":
            rrv_c_ErfExp = RooRealVar("rrv_c_ErfExp"+label+"_"+self.channel,"rrv_c_ErfExp"+label+"_"+self.channel,-0.007,-0.1,0.);
            rrv_offset_ErfExp = RooRealVar("rrv_offset_ErfExp"+label+"_"+self.channel,"rrv_offset_ErfExp"+label+"_"+self.channel,800.,10.,1400.);
            rrv_width_ErfExp = RooRealVar("rrv_width_ErfExp"+label+"_"+self.channel,"rrv_width_ErfExp"+label+"_"+self.channel,24.,10,150.);
            rrv_mean_gaus=RooRealVar("rrv_mean_gaus"+label+"_"+self.channel,"rrv_mean_gaus"+label+"_"+self.channel,700,500,1200);
            rrv_sigma_gaus=RooRealVar("rrv_sigma_gaus"+label+"_"+self.channel,"rrv_sigma_gaus"+label+"_"+self.channel,150,10,300);
            rrv_high = RooRealVar("rrv_high"+label+"_"+self.channel,"rrv_high"+label+"_"+self.channel,0.1,0.,1.);
            erfExp = ROOT.RooErfExpPdf("erfExp"+label+"_"+self.channel,"erfExp"+label+"_"+self.channel,rrv_x,rrv_c_ErfExp,rrv_offset_ErfExp,rrv_width_ErfExp);
            gaus = RooGaussian("gaus"+label+"_"+self.channel,"gaus"+label+"_"+self.channel, rrv_x,rrv_mean_gaus,rrv_sigma_gaus);
            model_pdf =RooAddPdf("model_pdf"+label+"_"+self.channel+mass_spectrum,"model_pdf"+label+"_"+self.channel+mass_spectrum,RooArgList(erfExp,gaus),RooArgList(rrv_high))

        if in_model_name == "ErfExpGaus_sp_v1":
            rrv_c_ErfExp = RooRealVar("rrv_c_ErfExp"+label+"_"+self.channel,"rrv_c_ErfExp"+label+"_"+self.channel,-0.007,-0.1,0.);
            rrv_width_ErfExp = RooRealVar("rrv_width_ErfExp"+label+"_"+self.channel,"rrv_width_ErfExp"+label+"_"+self.channel,24.,10,150.);
            rrv_mean_gaus=RooRealVar("rrv_mean_gaus"+label+"_"+self.channel,"rrv_mean_gaus"+label+"_"+self.channel,900,860,1200);
            rrv_sigma_gaus=RooRealVar("rrv_sigma_gaus"+label+"_"+self.channel,"rrv_sigma_gaus"+label+"_"+self.channel,150,10,300);
            rrv_high = RooRealVar("rrv_high"+label+"_"+self.channel,"rrv_high"+label+"_"+self.channel,0.1,0.,1.);
            erfExp = ROOT.RooErfExpPdf("erfExp"+label+"_"+self.channel,"erfExp"+label+"_"+self.channel,rrv_x,rrv_c_ErfExp,rrv_mean_gaus,rrv_width_ErfExp);
            gaus = RooGaussian("gaus"+label+"_"+self.channel,"gaus"+label+"_"+self.channel, rrv_x,rrv_mean_gaus,rrv_sigma_gaus);
            model_pdf =RooAddPdf("model_pdf"+label+"_"+self.channel+mass_spectrum,"model_pdf"+label+"_"+self.channel+mass_spectrum,RooArgList(erfExp,gaus),RooArgList(rrv_high))
    
        if in_model_name == "ErfExpGaus_v2":

            rrv_c_ErfExp = RooRealVar("rrv_c_ErfExp"+label+"_"+self.channel,"rrv_c_ErfExp"+label+"_"+self.channel,-0.05,-10.,0.);
            rrv_offset_ErfExp = RooRealVar("rrv_offset_ErfExp"+label+"_"+self.channel,"rrv_offset_ErfExp"+label+"_"+self.channel,100.,10.,140.);
            rrv_width_ErfExp = RooRealVar("rrv_width_ErfExp"+label+"_"+self.channel,"rrv_width_ErfExp"+label+"_"+self.channel,30.,10,100.);
            rrv_mean_gaus=RooRealVar("rrv_mean_gaus"+label+"_"+self.channel,"rrv_mean_gaus"+label+"_"+self.channel,84,78,88);
            rrv_sigma_gaus=RooRealVar("rrv_sigma_gaus"+label+"_"+self.channel,"rrv_sigma_gaus"+label+"_"+self.channel,7,4,10);
            rrv_high = RooRealVar("rrv_high"+label+"_"+self.channel,"rrv_high"+label+"_"+self.channel,200.,0.,1000.);
            model_pdf = ROOT.RooErfExp_Gaus_Pdf("model_pdf"+label+"_"+self.channel+mass_spectrum,"model_pdf"+label+"_"+self.channel+mass_spectrum, rrv_x,rrv_c_ErfExp,rrv_offset_ErfExp,rrv_width_ErfExp,rrv_mean_gaus,rrv_sigma_gaus,rrv_high );
    
        if in_model_name == "ErfExp2Gaus":
            rrv_c_ErfExp = RooRealVar("rrv_c_ErfExp"+label+"_"+self.channel,"rrv_c_ErfExp"+label+"_"+self.channel,-0.05,-0.2,0.);
            rrv_offset_ErfExp = RooRealVar("rrv_offset_ErfExp"+label+"_"+self.channel,"rrv_offset_ErfExp"+label+"_"+self.channel,100.,10.,140.);
            rrv_width_ErfExp = RooRealVar("rrv_width_ErfExp"+label+"_"+self.channel,"rrv_width_ErfExp"+label+"_"+self.channel,30.,10,100.);
            rrv_mean1_gaus=RooRealVar("rrv_mean1_gaus"+label+"_"+self.channel,"rrv_mean1_gaus"+label+"_"+self.channel,84,78,88);
            rrv_mean2_gaus=RooRealVar("rrv_mean2_gaus"+label+"_"+self.channel,"rrv_mean2_gaus"+label+"_"+self.channel,180,170,190);
            rrv_sigma1_gaus=RooRealVar("rrv_sigma1_gaus"+label+"_"+self.channel,"rrv_sigma1_gaus"+label+"_"+self.channel,7,4,10);
            rrv_sigma2_gaus=RooRealVar("rrv_sigma2_gaus"+label+"_"+self.channel,"rrv_sigma2_gaus"+label+"_"+self.channel,10,7,15);
            rrv_high1 = RooRealVar("rrv_high1"+label+"_"+self.channel,"rrv_high1"+label+"_"+self.channel,0.6,0.,1.);
            rrv_high2 = RooRealVar("rrv_high2"+label+"_"+self.channel,"rrv_high2"+label+"_"+self.channel,0.4,0.,1.);

            erfExp = ROOT.RooErfExpPdf("erfExp"+label+"_"+self.channel,"erfExp"+label+"_"+self.channel,rrv_x,rrv_c_ErfExp,rrv_offset_ErfExp,rrv_width_ErfExp);
            gaus1 = RooGaussian("gaus1"+label+"_"+self.channel,"gaus1"+label+"_"+self.channel, rrv_x,rrv_mean1_gaus,rrv_sigma1_gaus);
            gaus2 = RooGaussian("gaus2"+label+"_"+self.channel,"gaus2"+label+"_"+self.channel, rrv_x,rrv_mean2_gaus,rrv_sigma2_gaus);
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

            rrv_mean1_gaus=RooRealVar("rrv_mean1_gaus"+label+"_"+self.channel,"rrv_mean1_gaus"+label+"_"+self.channel,mean1_tmp, mean1_tmp-4, mean1_tmp+4);
            rrv_sigma1_gaus=RooRealVar("rrv_sigma1_gaus"+label+"_"+self.channel,"rrv_sigma1_gaus"+label+"_"+self.channel,sigma1_tmp, sigma1_tmp-4,sigma1_tmp+4 );
            gaus1 = RooGaussian("gaus1"+label+"_"+self.channel,"gaus1"+label+"_"+self.channel, rrv_x,rrv_mean1_gaus,rrv_sigma1_gaus);

            rrv_deltamean_gaus=RooRealVar("rrv_deltamean_gaus"+label+"_"+self.channel,"rrv_deltamean_gaus"+label+"_"+self.channel,deltamean_tmp, -4, deltamean_tmp+deltamean_tmp_err*4); 
            rrv_mean2_gaus =RooFormulaVar("rrv_mean2_gaus"+label+"_"+self.channel,"@0+@1",RooArgList(rrv_mean1_gaus, rrv_deltamean_gaus));
            rrv_scalesigma_gaus=RooRealVar("rrv_scalesigma_gaus"+label+"_"+self.channel,"rrv_scalesigma_gaus"+label+"_"+self.channel,scalesigma_tmp, scalesigma_tmp-scalesigma_tmp_err*8, scalesigma_tmp+scalesigma_tmp_err*8); 
            rrv_sigma2_gaus=RooFormulaVar("rrv_sigma2_gaus"+label+"_"+self.channel,"@0*@1", RooArgList(rrv_sigma1_gaus,rrv_scalesigma_gaus));
            gaus2 = RooGaussian("gaus2"+label+"_"+self.channel,"gaus2"+label+"_"+self.channel, rrv_x,rrv_mean2_gaus,rrv_sigma2_gaus);
            rrv_frac = RooRealVar("rrv_frac"+label+"_"+self.channel,"rrv_frac"+label+"_"+self.channel,frac_tmp, frac_tmp-frac_tmp_err*4, frac_tmp+frac_tmp_err*4);

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

            rrv_shift=RooRealVar("rrv_shift"+label+"_"+self.channel,"rrv_shift"+label+"_"+self.channel,10.8026)   # Z mass: 91.1876;  shift=91.1876-80.385=10.8026

            rrv_mean1_gaus=RooRealVar("rrv_mean1_gaus"+label+"_"+self.channel,"rrv_mean1_gaus"+label+"_"+self.channel,mean1_tmp, mean1_tmp-4, mean1_tmp+4);
            rrv_sigma1_gaus=RooRealVar("rrv_sigma1_gaus"+label+"_"+self.channel,"rrv_sigma1_gaus"+label+"_"+self.channel,sigma1_tmp, sigma1_tmp-4,sigma1_tmp+4 );
            gaus1 = RooGaussian("gaus1"+label+"_"+self.channel,"gaus1"+label+"_"+self.channel, rrv_x,rrv_mean1_gaus,rrv_sigma1_gaus);

            rrv_deltamean_gaus=RooRealVar("rrv_deltamean_gaus"+label+"_"+self.channel,"rrv_deltamean_gaus"+label+"_"+self.channel,0.,-8,10); 
            rrv_mean2_gaus =RooFormulaVar("rrv_mean2_gaus"+label+"_"+self.channel,"@0+@1",RooArgList(rrv_mean1_gaus, rrv_deltamean_gaus));
            rrv_scalesigma_gaus=RooRealVar("rrv_scalesigma_gaus"+label+"_"+self.channel,"rrv_scalesigma_gaus"+label+"_"+self.channel,scalesigma_tmp, scalesigma_tmp-scalesigma_tmp_err*4, scalesigma_tmp+scalesigma_tmp_err*4); 
            rrv_sigma2_gaus=RooFormulaVar("rrv_sigma2_gaus"+label+"_"+self.channel,"@0*@1", RooArgList(rrv_sigma1_gaus,rrv_scalesigma_gaus));
            gaus2 = RooGaussian("gaus2"+label+"_"+self.channel,"gaus2"+label+"_"+self.channel, rrv_x,rrv_mean2_gaus,rrv_sigma2_gaus);
            rrv_frac1 = RooRealVar("rrv_frac1"+label+"_"+self.channel,"rrv_frac1"+label+"_"+self.channel,frac_tmp, frac_tmp-frac_tmp_err*4, frac_tmp+frac_tmp_err*4);
            gausguas_1 =RooAddPdf("gausguas_1"+label+"_"+self.channel+mass_spectrum,"gausguas_1"+label+"_"+self.channel+mass_spectrum,RooArgList(gaus1,gaus2),RooArgList(rrv_frac1),1)

            rrv_mean3_gaus =RooFormulaVar("rrv_mean3_gaus"+label+"_"+self.channel,"@0+@1",RooArgList(rrv_mean1_gaus, rrv_shift));
            rrv_mean4_gaus =RooFormulaVar("rrv_mean4_gaus"+label+"_"+self.channel,"@0+@1",RooArgList(rrv_mean2_gaus, rrv_shift));
            gaus3 = RooGaussian("gaus3"+label+"_"+self.channel,"gaus3"+label+"_"+self.channel, rrv_x,rrv_mean3_gaus,rrv_sigma1_gaus);
            gaus4 = RooGaussian("gaus4"+label+"_"+self.channel,"gaus4"+label+"_"+self.channel, rrv_x,rrv_mean4_gaus,rrv_sigma2_gaus);
            gausguas_2 =RooAddPdf("gausguas_2"+label+"_"+self.channel+mass_spectrum,"gausguas_2"+label+"_"+self.channel+mass_spectrum,RooArgList(gaus3,gaus4),RooArgList(rrv_frac1),1)

            rrv_frac = RooRealVar("rrv_frac"+label+"_"+self.channel,"rrv_frac"+label+"_"+self.channel,0.74)#,0.5,1.0);
            model_pdf =RooAddPdf("model_pdf"+label+"_"+self.channel+mass_spectrum,"model_pdf"+label+"_"+self.channel+mass_spectrum,RooArgList(gausguas_1,gausguas_2),RooArgList(rrv_frac),1)


        if in_model_name == "2Gaus_ErfExp":
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

            rrv_mean1_gaus=RooRealVar("rrv_mean1_gaus"+label+"_"+self.channel,"rrv_mean1_gaus"+label+"_"+self.channel,mean1_tmp, mean1_tmp-4, mean1_tmp+4);
            rrv_sigma1_gaus=RooRealVar("rrv_sigma1_gaus"+label+"_"+self.channel,"rrv_sigma1_gaus"+label+"_"+self.channel,sigma1_tmp, sigma1_tmp-4,sigma1_tmp+4 );
            gaus1 = RooGaussian("gaus1"+label+"_"+self.channel,"gaus1"+label+"_"+self.channel, rrv_x,rrv_mean1_gaus,rrv_sigma1_gaus);

            rrv_deltamean_gaus=RooRealVar("rrv_deltamean_gaus"+label+"_"+self.channel,"rrv_deltamean_gaus"+label+"_"+self.channel,deltamean_tmp)#, deltamean_tmp, deltamean_tmp); 
            rrv_mean2_gaus =RooFormulaVar("rrv_mean2_gaus"+label+"_"+self.channel,"@0+@1",RooArgList(rrv_mean1_gaus, rrv_deltamean_gaus));
            rrv_scalesigma_gaus=RooRealVar("rrv_scalesigma_gaus"+label+"_"+self.channel,"rrv_scalesigma_gaus"+label+"_"+self.channel,scalesigma_tmp)#, scalesigma_tmp, scalesigma_tmp); 
            rrv_sigma2_gaus=RooFormulaVar("rrv_sigma2_gaus"+label+"_"+self.channel,"@0*@1", RooArgList(rrv_sigma1_gaus,rrv_scalesigma_gaus));
            gaus2 = RooGaussian("gaus2"+label+"_"+self.channel,"gaus2"+label+"_"+self.channel, rrv_x,rrv_mean2_gaus,rrv_sigma2_gaus);
            rrv_frac_2gaus = RooRealVar("rrv_frac_2gaus"+label+"_"+self.channel,"rrv_frac_2gaus"+label+"_"+self.channel,frac_tmp);#, frac_tmp-frac_tmp_err*4, frac_tmp+frac_tmp_err*4);


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

            rrv_c_ErfExp     = RooRealVar("rrv_c_ErfExp"+label+"_"+self.channel,"rrv_c_ErfExp"+label+"_"+self.channel,c0_tmp, c0_tmp-4e-2, c0_tmp+4e-2  );
            rrv_offset_ErfExp= RooRealVar("rrv_offset_ErfExp"+label+"_"+self.channel,"rrv_offset_ErfExp"+label+"_"+self.channel, offset_tmp)#, offset_tmp-offset_tmp_err*4,offset_tmp+offset_tmp_err*4);

            rrv_width_ErfExp = RooRealVar("rrv_width_ErfExp"+label+"_"+self.channel,"rrv_width_ErfExp"+label+"_"+self.channel, width_tmp, width_tmp-10, width_tmp+10);
            erfexp = ROOT.RooErfExpPdf("erfexp"+label+"_"+self.channel+mass_spectrum,"erfexp"+label+"_"+self.channel+mass_spectrum,rrv_x,rrv_c_ErfExp,rrv_offset_ErfExp,rrv_width_ErfExp);
 
            rrv_frac = RooRealVar("rrv_frac"+label+"_"+self.channel,"rrv_frac"+label+"_"+self.channel, 0.5,0.,1.);
            model_pdf =RooAddPdf("model_pdf"+label+"_"+self.channel+mass_spectrum,"model_pdf"+label+"_"+self.channel+mass_spectrum,RooArgList(erfexp, gaus1,gaus2),RooArgList(rrv_frac, rrv_frac_2gaus),1)

    
        if in_model_name == "ErfExpGausGaus":
            rrv_c_ErfExp = RooRealVar("rrv_c_ErfExp"+label+"_"+self.channel,"rrv_c_ErfExp"+label+"_"+self.channel,-0.1,-10.,0.);
            rrv_offset_ErfExp = RooRealVar("rrv_offset_ErfExp"+label+"_"+self.channel,"rrv_offset_ErfExp"+label+"_"+self.channel,100.,10.,140.);
            rrv_width_ErfExp = RooRealVar("rrv_width_ErfExp"+label+"_"+self.channel,"rrv_width_ErfExp"+label+"_"+self.channel,30.,10,100.);
            rrv_mean_voig=RooRealVar("rrv_mean_voig"+label+"_"+self.channel,"rrv_mean_voig"+label+"_"+self.channel,84,78,88);
            rrv_width_voig=RooRealVar("rrv_width_voig"+label+"_"+self.channel,"rrv_width_voig"+label+"_"+self.channel,7,1,20);
            rrv_sigma_voig=RooRealVar("rrv_sigma_voig"+label+"_"+self.channel,"rrv_sigma_voig"+label+"_"+self.channel,5,1,100);
            rrv_high1 = RooRealVar("rrv_high1"+label+"_"+self.channel,"rrv_high1"+label+"_"+self.channel,1,0.,200.);
            rrv_mean_gaus=RooRealVar("rrv_mean_gaus"+label+"_"+self.channel,"rrv_mean_gaus"+label+"_"+self.channel,174)#,160,187);
            rrv_sigma_gaus=RooRealVar("rrv_sigma_gaus"+label+"_"+self.channel,"rrv_sigma_gaus"+label+"_"+self.channel,20)#,0.1,100);
            rrv_high2 = RooRealVar("rrv_high2"+label+"_"+self.channel,"rrv_high2"+label+"_"+self.channel,0.)#,0.,0.);
            model_pdf = ROOT.RooErfExp_Voig_Gaus_Pdf("model_pdf"+label+"_"+self.channel+mass_spectrum,"model_pdf"+label+"_"+self.channel+mass_spectrum, rrv_x,rrv_c_ErfExp,rrv_offset_ErfExp,rrv_width_ErfExp,rrv_mean_voig,rrv_width_voig,rrv_sigma_voig,rrv_high1,rrv_mean_gaus,rrv_sigma_gaus,rrv_high2 );

        if in_model_name == "User1":
            rrv_p0=RooRealVar("rrv_p0_User1"+label+"_"+self.channel,"rrv_p0_User1"+label+"_"+self.channel, 30,  10, 90);
            rrv_p1=RooRealVar("rrv_p1_User1"+label+"_"+self.channel,"rrv_p1_User1"+label+"_"+self.channel, -4,  -9, -2);
            #rrv_p2=RooRealVar("rrv_p2_User1"+label+"_"+self.channel,"rrv_p2_User1"+label+"_"+self.channel, 0)#,-100,100)#,200,1000)#,50,1000)#,-200,200);
            model_pdf=RooUser1Pdf("model_pdf"+label+"_"+self.channel+mass_spectrum,"model_pdf"+label+"_"+self.channel+mass_spectrum,rrv_x,rrv_p0,rrv_p1);

        if in_model_name == "QCD":
            rrv_p0=RooRealVar("rrv_p0_QCD"+label+"_"+self.channel,"rrv_p0_QCD"+label+"_"+self.channel,  0,-200,200);
            rrv_p1=RooRealVar("rrv_p1_QCD"+label+"_"+self.channel,"rrv_p1_QCD"+label+"_"+self.channel,  0,-200,200);
            rrv_p2=RooRealVar("rrv_p2_QCD"+label+"_"+self.channel,"rrv_p2_QCD"+label+"_"+self.channel,  0,-200,200);
            model_pdf=RooQCDPdf("model_pdf"+label+"_"+self.channel+mass_spectrum,"model_pdf"+label+"_"+self.channel+mass_spectrum,rrv_x,rrv_p0,rrv_p1,rrv_p2);

        if in_model_name == "QCD_v2":#can replace exp 
            rrv_p0=RooRealVar("rrv_p0_QCD"+label+"_"+self.channel,"rrv_p0_QCD"+label+"_"+self.channel, -15,-50,0);
            rrv_p1=RooRealVar("rrv_p1_QCD"+label+"_"+self.channel,"rrv_p1_QCD"+label+"_"+self.channel,  20,0,250);
            rrv_p2=RooRealVar("rrv_p2_QCD"+label+"_"+self.channel,"rrv_p2_QCD"+label+"_"+self.channel,0,-20,20);
            model_pdf=RooQCDPdf("model_pdf"+label+"_"+self.channel+mass_spectrum,"model_pdf"+label+"_"+self.channel+mass_spectrum,rrv_x,rrv_p0,rrv_p1,rrv_p2);

        if in_model_name == "Pow" or in_model_name == "Pow_sr" :#can replace exp
            rrv_c=RooRealVar("rrv_c_Pow"+label+"_"+self.channel,"rrv_c_Pow"+label+"_"+self.channel, -5, -20, 0);
            model_pdf=RooPowPdf("model_pdf"+label+"_"+self.channel+mass_spectrum,"model_pdf"+label+"_"+self.channel+mass_spectrum,rrv_x, rrv_c );
 
        if in_model_name == "Pow2":
            rrv_c0=RooRealVar("rrv_c0_Pow2"+label+"_"+self.channel,"rrv_c0_Pow2"+label+"_"+self.channel, 5, 0, 20);
            rrv_c1=RooRealVar("rrv_c1_Pow2"+label+"_"+self.channel,"rrv_c1_Pow2"+label+"_"+self.channel, 0, -5 , 5);
            model_pdf=RooPow2Pdf("model_pdf"+label+"_"+self.channel+mass_spectrum,"model_pdf"+label+"_"+self.channel+mass_spectrum, rrv_x, rrv_c0, rrv_c1 );

        if in_model_name == "ErfPow_v1":#can replace erf*exp 
            rrv_c=RooRealVar("rrv_c_ErfPow"+label+"_"+self.channel,"rrv_c_ErfPow"+label+"_"+self.channel, -5,-10,0);
            rrv_offset=RooRealVar("rrv_offset_ErfPow"+label+"_"+self.channel,"rrv_offset_ErfPow"+label+"_"+self.channel, 450,350,550);
            rrv_width=RooRealVar("rrv_width_ErfPow"+label+"_"+self.channel,"rrv_width_ErfPow"+label+"_"+self.channel,50,20,90);
            model_pdf=RooErfPowPdf("model_pdf"+label+"_"+self.channel+mass_spectrum,"model_pdf"+label+"_"+self.channel+mass_spectrum,rrv_x,rrv_c,rrv_offset,rrv_width);

        if in_model_name == "ErfPow2_v1":#can replace erf*exp 
            rrv_c0=RooRealVar("rrv_c0_ErfPow2"+label+"_"+self.channel,"rrv_c0_ErfPow2"+label+"_"+self.channel,14,1,30);
            rrv_c1=RooRealVar("rrv_c1_ErfPow2"+label+"_"+self.channel,"rrv_c1_ErfPow2"+label+"_"+self.channel, 5,-5,10);
            rrv_offset=RooRealVar("rrv_offset_ErfPow2"+label+"_"+self.channel,"rrv_offset_ErfPow2"+label+"_"+self.channel, 450,400,520);
            rrv_width=RooRealVar("rrv_width_ErfPow2"+label+"_"+self.channel,"rrv_width_ErfPow2"+label+"_"+self.channel,30,10,80);
            model_pdf=RooErfPow2Pdf("model_pdf"+label+"_"+self.channel+mass_spectrum,"model_pdf"+label+"_"+self.channel+mass_spectrum,rrv_x,rrv_c0,rrv_c1,rrv_offset,rrv_width);

        if in_model_name == "ErfPow2_v1_sr":#can replace erf*exp 
            rrv_c0=RooRealVar("rrv_c0_ErfPow2"+label+"_"+self.channel,"rrv_c0_ErfPow2"+label+"_"+self.channel, 4,2, 8);
            rrv_c1=RooRealVar("rrv_c1_ErfPow2"+label+"_"+self.channel,"rrv_c1_ErfPow2"+label+"_"+self.channel, -0.5,-2,0);
            rrv_offset=RooRealVar("rrv_offset_ErfPow2"+label+"_"+self.channel,"rrv_offset_ErfPow2"+label+"_"+self.channel, 490,440,520);
            rrv_width=RooRealVar("rrv_width_ErfPow2"+label+"_"+self.channel,"rrv_width_ErfPow2"+label+"_"+self.channel,50,30,80);
            model_pdf=RooErfPow2Pdf("model_pdf"+label+"_"+self.channel+mass_spectrum,"model_pdf"+label+"_"+self.channel+mass_spectrum,rrv_x,rrv_c0,rrv_c1,rrv_offset,rrv_width);

        if in_model_name == "ErfPowExp_v1":#can replace erf*exp
            if ( ismc == 1 ):
              rrv_c0=RooRealVar("rrv_c0_ErfPowExp"+label+"_"+self.channel,"rrv_c0_ErfPowExp"+label+"_"+self.channel,13,5,40);
              rrv_c1=RooRealVar("rrv_c1_ErfPowExp"+label+"_"+self.channel,"rrv_c1_ErfPowExp"+label+"_"+self.channel, 2,0,4);
              rrv_offset=RooRealVar("rrv_offset_ErfPowExp"+label+"_"+self.channel,"rrv_offset_ErfPowExp"+label+"_"+self.channel, 450,420,520);
              rrv_width=RooRealVar("rrv_width_ErfPowExp"+label+"_"+self.channel,"rrv_width_ErfPowExp"+label+"_"+self.channel,30,10,80);
                                                
            else :
              rrv_c0=RooRealVar("rrv_c0_ErfPowExp"+label+"_"+self.channel,"rrv_c0_ErfPowExp"+label+"_"+self.channel,11,5,20);
              rrv_c1=RooRealVar("rrv_c1_ErfPowExp"+label+"_"+self.channel,"rrv_c1_ErfPowExp"+label+"_"+self.channel, 0,-2,2);
              rrv_offset=RooRealVar("rrv_offset_ErfPowExp"+label+"_"+self.channel,"rrv_offset_ErfPowExp"+label+"_"+self.channel, 470,420,520);
              rrv_width=RooRealVar("rrv_width_ErfPowExp"+label+"_"+self.channel,"rrv_width_ErfPowExp"+label+"_"+self.channel,40,30,50);

            model_pdf=RooErfPowExpPdf("model_pdf"+label+"_"+self.channel+mass_spectrum,"model_pdf"+label+"_"+self.channel+mass_spectrum,rrv_x,rrv_c0,rrv_c1,rrv_offset,rrv_width);

        if in_model_name == "GausExp_v1" :

            rrv_mean_GausExp=RooRealVar("rrv_mean_GausExp"+label+"_"+self.channel,"rrv_mean_GausExp"+label+"_"+self.channel,500.,400.,600.);
            rrv_sigma_GausExp=RooRealVar("rrv_sigma_GausExp"+label+"_"+self.channel,"rrv_sigma_GausExp"+label+"_"+self.channel, 50, 10 ,100 );
            rrv_c_GausExp = RooRealVar("rrv_c_GausExp"+label+"_"+self.channel,"rrv_c_GausExp"+label+"_"+self.channel,-0.04,-1.5,0.);
                    
            model_pdf = RooGausExpPdf("model_pdf"+label+"_"+self.channel+mass_spectrum,"model_pdf"+label+"_"+self.channel+mass_spectrum, rrv_x, rrv_c_GausExp, rrv_mean_GausExp, rrv_sigma_GausExp );
       
        if in_model_name == "ErfPowExp_v1_sr":#can replace erf*exp 
            rrv_c0=RooRealVar("rrv_c0_ErfPowExp"+label+"_"+self.channel,"rrv_c0_ErfPowExp"+label+"_"+self.channel,6,2,15);
            rrv_c1=RooRealVar("rrv_c1_ErfPowExp"+label+"_"+self.channel,"rrv_c1_ErfPowExp"+label+"_"+self.channel, -1,-3,2);
            rrv_offset=RooRealVar("rrv_offset_ErfPowExp"+label+"_"+self.channel,"rrv_offset_ErfPowExp"+label+"_"+self.channel, 490,440,520);
            rrv_width=RooRealVar("rrv_width_ErfPowExp"+label+"_"+self.channel,"rrv_width_ErfPowExp"+label+"_"+self.channel,50,30,70);
            model_pdf=RooErfPowExpPdf("model_pdf"+label+"_"+self.channel+mass_spectrum,"model_pdf"+label+"_"+self.channel+mass_spectrum,rrv_x,rrv_c0,rrv_c1,rrv_offset,rrv_width);

        if in_model_name == "ErfPowExp_v1_0":#difference inital value
            rrv_c0=RooRealVar("rrv_c0_ErfPowExp"+label+"_"+self.channel,"rrv_c0_ErfPowExp"+label+"_"+self.channel,20,15,40);
            rrv_c1=RooRealVar("rrv_c1_ErfPowExp"+label+"_"+self.channel,"rrv_c1_ErfPowExp"+label+"_"+self.channel, 1.6,0.5,5);
            rrv_offset=RooRealVar("rrv_offset_ErfPowExp"+label+"_"+self.channel,"rrv_offset_ErfPowExp"+label+"_"+self.channel, 470,420,520);
            rrv_width=RooRealVar("rrv_width_ErfPowExp"+label+"_"+self.channel,"rrv_width_ErfPowExp"+label+"_"+self.channel,47,30,60);
            model_pdf=RooErfPowExpPdf("model_pdf"+label+"_"+self.channel+mass_spectrum,"model_pdf"+label+"_"+self.channel+mass_spectrum,rrv_x,rrv_c0,rrv_c1,rrv_offset,rrv_width);

        if in_model_name == "Keys":
            rdataset=self.workspace4fit_.data("rdataset_%s_signal_region_mlvj"%(self.signal_sample))
            model_pdf = RooKeysPdf("model_pdf"+label+"_"+self.channel+mass_spectrum,"model_pdf"+label+"_"+self.channel+mass_spectrum, rrv_x,rdataset);

        getattr(self.workspace4fit_,"import")(model_pdf)
        return self.workspace4fit_.pdf("model_pdf"+label+"_"+self.channel+mass_spectrum)

    ##################### ---------------------------------------------------
    def addConstraint(self, rrv_x, x_mean, x_sigma, ConstraintsList):
            rrv_x_mean = RooRealVar(rrv_x.GetName()+"_mean",rrv_x.GetName()+"_mean",x_mean );
            rrv_x_sigma = RooRealVar(rrv_x.GetName()+"_sigma",rrv_x.GetName()+"_sigma",x_sigma );
            constrainpdf_x=RooGaussian("constrainpdf_"+rrv_x.GetName(),"constrainpdf_"+rrv_x.GetName(),rrv_x, rrv_x_mean, rrv_x_sigma);
            getattr(self.workspace4fit_,"import")(constrainpdf_x)
            ConstraintsList.append(constrainpdf_x.GetName()); 

    ##################### ---------------------------------------------------
    def make_Model(self, label, in_model_name, mass_spectrum="_mj", ConstraintsList=[],ismc_wjet=0):

        rrv_number = RooRealVar("rrv_number"+label+"_"+self.channel+mass_spectrum,"rrv_number"+label+"_"+self.channel+mass_spectrum,500,0.,1e7);
        model_pdf  = self.make_Pdf(label,in_model_name,mass_spectrum,ConstraintsList,ismc_wjet)
        model_pdf.Print();
        model = RooExtendPdf("model"+label+"_"+self.channel+mass_spectrum,"model"+label+"_"+self.channel+mass_spectrum, model_pdf, rrv_number );
        getattr(self.workspace4fit_,"import")(rrv_number)
        getattr(self.workspace4fit_,"import")(model)
        model.Print();
        print "model"+label+"_"+self.channel+mass_spectrum 
        self.workspace4fit_.pdf("model"+label+"_"+self.channel+mass_spectrum).Print();
        return self.workspace4fit_.pdf("model"+label+"_"+self.channel+mass_spectrum);

    ##################### ---------------------------------------------------

    def get_mj_Model(self,label):
        return self.workspace4fit_.pdf("model"+label+"_"+self.channel+"_mj")

    ##################### ---------------------------------------------------
    def get_General_mj_Model(self, label ):
        rdataset_General_mj=self.workspace4fit_.data("rdataset%s_%s_mj"%(label,self.channel))
        model_General=self.get_mj_Model(label);
        parameters_General=model_General.getParameters(rdataset_General_mj);
        par=parameters_General.createIterator();
        par.Reset();
        param=par.Next()
        while (param):
            if (TString(label).Contains("VV") or TString(label).Contains("STop") or TString(label).Contains("TTbar")):
                param.Print();
            param.setConstant(kTRUE);
            param=par.Next()
        return self.workspace4fit_.pdf("model%s_%s_mj"%(label,self.channel))

    ###################### ---------------------------------------------------
    def get_TTbar_mj_Model(self,label="_TTbar"):
        return self.get_General_mj_Model(label);
    ###################### ---------------------------------------------------
    def get_STop_mj_Model(self,label="_STop"):
        return self.get_General_mj_Model(label);
    ###################### ---------------------------------------------------
    def get_VV_mj_Model(self,label="_VV"):
        return self.get_General_mj_Model(label);

    ##################### ---------------------------------------------------
    def get_WJets_mj_Model(self,label):
        rdataset_WJets_mj=self.workspace4fit_.data("rdataset%s_%s_mj"%(label,self.channel))
        model_WJets=self.get_mj_Model(label);
        parameters_WJets=model_WJets.getParameters(rdataset_WJets_mj);
        par=parameters_WJets.createIterator(); par.Reset();
        param=par.Next()
        while (param):
            paraName=TString(param.GetName());
            if ( paraName.Contains("rrv_width_ErfExp_WJets") or paraName.Contains("rrv_offset_ErfExp_WJets") or paraName.Contains("rrv_p1_User1_WJets") or paraName.Contains("rrv_p1_User1_WJets")) :param.setConstant(kTRUE);
            else: param.setConstant(0);

            #param.setConstant(0);
            param=par.Next()
        return self.workspace4fit_.pdf("model%s_%s_mj"%(label,self.channel))

    ##################### ---------------------------------------------------
    def get_mlvj_Model(self,label, mlvj_region):
        return self.workspace4fit_.pdf("model"+label+mlvj_region+"_"+self.channel+"_mlvj");

    ##################### ---------------------------------------------------
    def get_General_mlvj_Model(self, label, mlvj_region="_signal_region"):
        rdataset_General_mlvj=self.workspace4fit_.data("rdataset%s%s_%s_mlvj"%(label, mlvj_region,self.channel))
        model_General=self.get_mlvj_Model(label,mlvj_region);
        model_General.Print()
        parameters_General=model_General.getParameters(rdataset_General_mlvj);
        par=parameters_General.createIterator(); par.Reset();
        param=par.Next()
        while (param):
            param.setConstant(kTRUE);
            param.Print();
            param=par.Next()
        return self.get_mlvj_Model(label,mlvj_region);

    ##################### ---------------------------------------------------
    def get_TTbar_mlvj_Model(self, mlvj_region="_signal_region"):
        return self.get_General_mlvj_Model("_TTbar",mlvj_region);
    ##################### ---------------------------------------------------
    def get_STop_mlvj_Model(self, mlvj_region="_signal_region"):
        return self.get_General_mlvj_Model("_STop",mlvj_region);

    ##################### ---------------------------------------------------
    def get_signal_mlvj_Model(self, mlvj_region="_signal_region"):
        return self.get_General_mlvj_Model("_%s"%(self.signal_sample),mlvj_region);

    ##################### ---------------------------------------------------
    def get_VV_mlvj_Model(self, mlvj_region="_signal_region"):
        return self.get_General_mlvj_Model("_VV",mlvj_region);

    ##################### ---------------------------------------------------

    def get_WJets_mlvj_Model(self, mlvj_region="_signal_region"):
        print "get_WJets_mlvj_Model"
        rdataset_WJets_mlvj=self.workspace4fit_.data("rdataset_WJets%s_mlvj"%(mlvj_region))
        model_WJets=self.get_mlvj_Model("_WJets0",mlvj_region);
        model_WJets.Print()
        rdataset_WJets_mlvj.Print()
        parameters_WJets=model_WJets.getParameters(rdataset_WJets_mlvj);
        par=parameters_WJets.createIterator();
        par.Reset();
        param=par.Next()
        while (param):
            paraName=TString(param.GetName());
            param.Print();
            if paraName.Contains("rrv_number_WJets"): 
                if self.workspace4fit_.var("rrv_number_WJets_in_mj%s_from_fitting_%s"%(mlvj_region,self.channel)):
                    self.workspace4fit_.var("rrv_number_WJets_in_mj%s_from_fitting_%s"%(mlvj_region,self.channel)).Print()
                    param.setVal( self.workspace4fit_.var("rrv_number_WJets_in_mj%s_from_fitting_%s"%(mlvj_region,self.channel)).getVal() )
                if mlvj_region=="_signal_region": param.setConstant(kTRUE);
            param.Print();
            param=par.Next()
	    return self.get_mlvj_Model("_WJets0",mlvj_region);

    ##################### ---------------------------------------------------
    def fix_Model(self, label, mlvj_region="_signal_region",mass_spectrum="_mlvj"):
        rdataset=self.workspace4fit_.data("rdataset%s%s_%s%s"%(label,mlvj_region,self.channel,mass_spectrum))
        model=self.get_mlvj_Model(label,mlvj_region);
        parameters=model.getParameters(rdataset);
        par=parameters.createIterator(); par.Reset();
        param=par.Next()
        while (param):
            param.setConstant(kTRUE);
            param=par.Next()

    ##################### ---------------------------------------------------
    def fix_Pdf(self,model_pdf,argset_notparameter):
        model_pdf.Print()
        parameters=model_pdf.getParameters(argset_notparameter);
        par=parameters.createIterator(); par.Reset();
        param=par.Next()
        while (param):
            param.setConstant(kTRUE);
            param.Print();
            param=par.Next()

    ##################### ---------------------------------------------------
    def ShowParam_Pdf(self,model_pdf,argset_notparameter):
        model_pdf.Print()
        parameters=model_pdf.getParameters(argset_notparameter);
        par=parameters.createIterator(); par.Reset();
        param=par.Next()
        while (param):
            #param.Print();
            if not param.isConstant():
                param.Print();
                if (param.getVal()-param.getMin())< param.getError()*1 or (param.getMax()- param.getVal())< param.getError()*1: 
                    #print param.getVal()-param.getMin(), param.getError()*2, (param.getMax()- param.getVal()); 
                    param.Print();
                    #raw_input("ENTER");
            param=par.Next()

    ###################### --------------------------------------------------------
            
    def get_WJets_mlvj_correction_sb_lo_to_signal_region(self,label,mlvj_region,mlvj_model):#exo-vv method: extract M_lvj shape of signal_region from sb_lo

        tmp_Style=self.tdrStyle.Clone("tmp_Style");
        tmp_Style.SetPadRightMargin(0.08); 
        tmp_Style.SetPadTickY(0);
        tmp_Style.cd();

        print "get_WJets_mlvj_correction%s_to_signal_region"%(mlvj_region);

        rrv_x = self.workspace4fit_.var("rrv_mass_lvj"); 
        rdataset_WJets_sb_lo_mlvj=self.workspace4fit_.data("rdataset4fit%s%s_%s_mlvj"%(label,mlvj_region,self.channel))
        rdataset_WJets_signal_region_mlvj=self.workspace4fit_.data("rdataset4fit%s_signal_region_%s_mlvj"%(label,self.channel))
        mplot = rrv_x.frame(RooFit.Title("correlation_pdf"), RooFit.Bins(int(rrv_x.getBins()/self.narrow_factor))) ; mplot.GetYaxis().SetTitle("arbitrary unit");

        if mlvj_model=="ErfExp_v1":
            rrv_c_sb      = self.workspace4fit_.var("rrv_c_ErfExp%s%s_%s"%(label,mlvj_region,self.channel));
            rrv_offset_sb = self.workspace4fit_.var("rrv_offset_ErfExp%s%s_%s"%(label,mlvj_region,self.channel));
            rrv_width_sb  = self.workspace4fit_.var("rrv_width_ErfExp%s%s_%s"%(label,mlvj_region,self.channel));
            rrv_delta_c   = RooRealVar("rrv_delta_c_ErfExp%s%s_%s"%(label,mlvj_region,self.channel),"rrv_delta_c_ErfExp%s%s_%s"%(label,mlvj_region,self.channel),0., -100*rrv_c_sb.getError(),100*rrv_c_sb.getError()); 
            rrv_delta_offset = RooRealVar("rrv_delta_offset_ErfExp%s%s_%s"%(label,mlvj_region,self.channel),"rrv_delta_offset_ErfExp%s_%s"%(label,mlvj_region,self.channel),0., -100*rrv_offset_sb.getError(),100*rrv_offset_sb.getError()); 
            rrv_delta_width = RooRealVar("rrv_delta_width_ErfExp%s%s_%s"%(label,mlvj_region,self.channel),"rrv_delta_width_ErfExp%s%s_%s"%(label,mlvj_region,self.channel),0., -100*rrv_width_sb.getError(),100*rrv_width_sb.getError()); 
            rrv_c_sr =RooFormulaVar("rrv_c_sr%s%s_%s"%(label,mlvj_region,self.channel), "@0+@1",RooArgList(rrv_c_sb, rrv_delta_c ) );
            rrv_offset_sr =RooFormulaVar("rrv_offset_sr%s%s_%s"%(label,mlvj_region,self.channel), "@0+@1",RooArgList(rrv_offset_sb, rrv_delta_offset ) );
            rrv_width_sr =RooFormulaVar("rrv_width_sr%s%s_%s"%(label,mlvj_region,self.channel), "@0+@1",RooArgList(rrv_width_sb, rrv_delta_width ) );
            correct_factor_pdf = RooAlpha("correct_factor_pdf","correct_factor_pdf", rrv_x, rrv_c_sr, rrv_offset_sr,rrv_width_sr, rrv_c_sb, rrv_offset_sb, rrv_width_sb, rrv_x.getMin(), rrv_x.getMax());

        elif mlvj_model=="ErfPow_v1":

            rrv_c_sb       = self.workspace4fit_.var("rrv_c_ErfPow%s%s_%s"%(label,mlvj_region,self.channel));
            rrv_offset_sb  = self.workspace4fit_.var("rrv_offset_ErfPow%s%s_%s"%(label,mlvj_region,self.channel));
            rrv_width_sb   = self.workspace4fit_.var("rrv_width_ErfPow%s%s_%s"%(label,mlvj_region,self.channel));
            rrv_delta_c    = RooRealVar("rrv_delta_c_ErfPow%s%s_%s"%(label,mlvj_region,self.channel),"rrv_delta_c_ErfPow%s%s_%s"%(label,mlvj_region,self.channel),0., -100*rrv_c_sb.getError(),100*rrv_c_sb.getError()); 
            rrv_delta_offset = RooRealVar("rrv_delta_offset_ErfPow%s%s_%s"%(label,mlvj_region,self.channel),"rrv_delta_offset_ErfPow%s%s_%s"%(label,mlvj_region,self.channel),0., -100*rrv_offset_sb.getError(),100*rrv_offset_sb.getError()); 
            rrv_delta_width = RooRealVar("rrv_delta_width_ErfPow%s%s_%s"%(label,mlvj_region,self.channel),"rrv_delta_width_ErfPow%s%s_%s"%(label,mlvj_region,self.channel),0., -100*rrv_width_sb.getError(),100*rrv_width_sb.getError()); 
            rrv_c_sr =RooFormulaVar("rrv_c_sr%s%s_%s"%(label,mlvj_region,self.channel), "@0+@1",RooArgList(rrv_c_sb, rrv_delta_c ) );
            rrv_offset_sr =RooFormulaVar("rrv_offset_sr%s%s_%s"%(label,mlvj_region,self.channel), "@0+@1",RooArgList(rrv_offset_sb, rrv_delta_offset ) );
            rrv_width_sr =RooFormulaVar("rrv_width_sr%s%s_%s"%(label,mlvj_region,self.channel), "@0+@1",RooArgList(rrv_width_sb, rrv_delta_width ) );
            correct_factor_pdf = RooAlpha4ErfPowPdf("correct_factor_pdf","correct_factor_pdf", rrv_x, rrv_c_sr, rrv_offset_sr,rrv_width_sr, rrv_c_sb, rrv_offset_sb, rrv_width_sb);

        elif mlvj_model=="ErfPow2_v1":

            rrv_c0_sb     =self.workspace4fit_.var("rrv_c0_ErfPow2%s%s_%s"%(label,mlvj_region,self.channel));
            rrv_c1_sb     =self.workspace4fit_.var("rrv_c1_ErfPow2%%s_%s"%(label,mlvj_region,self.channel));
            rrv_offset_sb=self.workspace4fit_.var("rrv_offset_ErfPow2%s%s_%s"%(label,mlvj_region,self.channel));
            rrv_width_sb =self.workspace4fit_.var("rrv_width_ErfPow2%s_s_%s"%(label,mlvj_region,self.channel));
            rrv_delta_c0 = RooRealVar("rrv_delta_c0_ErfPow2%s%s_%s"%(label,mlvj_region,self.channel),"rrv_delta_c0_ErfPow2%s%s_%s"%(label,mlvj_region,self.channel),-8, -20 ,0)#,0., -100*rrv_c0_sb.getError(),100*rrv_c0_sb.getError()); 
            rrv_delta_c1 = RooRealVar("rrv_delta_c1_ErfPow2%s%s_%s"%(label,mlvj_region,self.channel),"rrv_delta_c1_ErfPow2%s%s_%s"%(label,mlvj_region,self.channel),0., -5, 5);#-100*rrv_c1_sb.getError(),100*rrv_c1_sb.getError()); 
            rrv_delta_offset = RooRealVar("rrv_delta_offset_ErfPow2%s%s_%s"%(label,mlvj_region,self.channel),"rrv_delta_offset_ErfPow2%s%s_%s"%(label,mlvj_region,self.channel),30., 1.,80 );#0., -100*rrv_offset_sb.getError(),100*rrv_offset_sb.getError()); 
            rrv_delta_width = RooRealVar("rrv_delta_width_ErfPow2%s%s_%s"%(label,mlvj_region,self.channel),"rrv_delta_width_ErfPow2%s%s_%s"%(label,mlvj_region,self.channel),15,1.,100*rrv_width_sb.getError()); #0., -100*rrv_width_sb.getError(),100*rrv_width_sb.getError()); 
            rrv_c0_sr =RooFormulaVar("rrv_c0_sr%s%s_%s"%(label,mlvj_region,self.channel), "@0+@1",RooArgList(rrv_c0_sb, rrv_delta_c0 ) );
            rrv_c1_sr =RooFormulaVar("rrv_c1_sr%s%s_%s"%(label,mlvj_region,self.channel), "@0+@1",RooArgList(rrv_c1_sb, rrv_delta_c1 ) );
            rrv_offset_sr =RooFormulaVar("rrv_offset_sr%s%s_%s"%(label,mlvj_region,self.channel), "@0+@1",RooArgList(rrv_offset_sb, rrv_delta_offset ) );
            rrv_width_sr =RooFormulaVar("rrv_width_sr%s%s_%s"%(label,mlvj_region,self.channel), "@0+@1",RooArgList(rrv_width_sb, rrv_delta_width ) );
            correct_factor_pdf = RooAlpha4ErfPow2Pdf("correct_factor_pdf","correct_factor_pdf", rrv_x, rrv_c0_sr, rrv_c1_sr, rrv_offset_sr,rrv_width_sr, rrv_c0_sb, rrv_c1_sb, rrv_offset_sb, rrv_width_sb);

        elif mlvj_model=="ErfPowExp_v1":

            rrv_c0_sb     =self.workspace4fit_.var("rrv_c0_ErfPowExp%s%s_%s"%(label,mlvj_region,self.channel));
            rrv_c1_sb     =self.workspace4fit_.var("rrv_c1_ErfPowExp%s%s_%s"%(label,mlvj_region,self.channel));
            rrv_offset_sb=self.workspace4fit_.var("rrv_offset_ErfPowExp%s%s_%s"%(label,mlvj_region,self.channel));
            rrv_width_sb =self.workspace4fit_.var("rrv_width_ErfPowExp%s%s_%s"%(label,mlvj_region,self.channel));
            rrv_delta_c0 = RooRealVar("rrv_delta_c0_ErfPowExp%s%s_%s"%(label,mlvj_region,self.channel),"rrv_delta_c0_ErfPowExp%s%s_%s"%(label,mlvj_region,self.channel),
                    self.workspace4fit_.var("rrv_c0_ErfPowExp%s_signal_region_%s"%(label,self.channel)).getVal()-rrv_c0_sb.getVal(),
                    self.workspace4fit_.var("rrv_c0_ErfPowExp%s_signal_region_%s"%(label,self.channel)).getVal()-rrv_c0_sb.getVal()-4*rrv_c0_sb.getError(),
                    self.workspace4fit_.var("rrv_c0_ErfPowExp%s_signal_region_%s"%(label,self.channel)).getVal()-rrv_c0_sb.getVal()+4*rrv_c0_sb.getError() )
            rrv_delta_c1 = RooRealVar("rrv_delta_c1_ErfPowExp%s%s_%s"%(label,mlvj_region,self.channel),"rrv_delta_c1_ErfPowExp%s%s_%s"%(label,mlvj_region,self.channel),
                    self.workspace4fit_.var("rrv_c1_ErfPowExp%s_signal_region_%s"%(label,self.channel)).getVal()-rrv_c1_sb.getVal(),
                    self.workspace4fit_.var("rrv_c1_ErfPowExp%s_signal_region_%s"%(label,self.channel)).getVal()-rrv_c1_sb.getVal()-4*rrv_c1_sb.getError(),
                    self.workspace4fit_.var("rrv_c1_ErfPowExp%s_signal_region_%s"%(label,self.channel)).getVal()-rrv_c1_sb.getVal()+4*rrv_c1_sb.getError() )
            rrv_delta_offset = RooRealVar("rrv_delta_offset_ErfPowExp%s%s_%s"%(label,mlvj_region,self.channel),"rrv_delta_offset_ErfPowExp%s%s_%s"%(label,mlvj_region,self.channel),
                    self.workspace4fit_.var("rrv_offset_ErfPowExp%s_signal_region_%s"%(label,self.channel)).getVal()-rrv_offset_sb.getVal(),
                    self.workspace4fit_.var("rrv_offset_ErfPowExp%s_signal_region_%s"%(label,self.channel)).getVal()-rrv_offset_sb.getVal()-4*rrv_offset_sb.getError(),
                    self.workspace4fit_.var("rrv_offset_ErfPowExp%s_signal_region_%s"%(label,self.channel)).getVal()-rrv_offset_sb.getVal()+4*rrv_offset_sb.getError() )
            rrv_delta_width = RooRealVar("rrv_delta_width_ErfPowExp%s%s_%s"%(label,mlvj_region,self.channel),"rrv_delta_width_ErfPowExp%s%s_%s"%(label,mlvj_region,self.channel),
                    self.workspace4fit_.var("rrv_width_ErfPowExp%s_signal_region_%s"%(label,self.channel)).getVal()-rrv_width_sb.getVal(),
                    self.workspace4fit_.var("rrv_width_ErfPowExp%s_signal_region_%s"%(label,self.channel)).getVal()-rrv_width_sb.getVal()-4*rrv_width_sb.getError(),
                    self.workspace4fit_.var("rrv_width_ErfPowExp%s_signal_region_%s"%(label,self.channel)).getVal()-rrv_width_sb.getVal()+4*rrv_width_sb.getError() )
            rrv_c0_sr =RooFormulaVar("rrv_c0_sr%s%s_%s"%(label,mlvj_region,self.channel), "@0+@1",RooArgList(rrv_c0_sb, rrv_delta_c0 ) );
            rrv_c1_sr =RooFormulaVar("rrv_c1_sr%s%s_%s"%(label,mlvj_region,self.channel), "@0+@1",RooArgList(rrv_c1_sb, rrv_delta_c1 ) );
            rrv_offset_sr =RooFormulaVar("rrv_offset_sr%s%s_%s"%(label,mlvj_region,self.channel), "@0+@1",RooArgList(rrv_offset_sb, rrv_delta_offset ) );
            rrv_width_sr =RooFormulaVar("rrv_width_sr%s%s_%s"%(label,mlvj_region,self.channel), "@0+@1",RooArgList(rrv_width_sb, rrv_delta_width ) );
            correct_factor_pdf = RooAlpha4ErfPowExpPdf("correct_factor_pdf","correct_factor_pdf", rrv_x, rrv_c0_sr, rrv_c1_sr, rrv_offset_sr,rrv_width_sr, rrv_c0_sb, rrv_c1_sb, rrv_offset_sb, rrv_width_sb);


        elif mlvj_model=="Exp":
            rrv_c_sb     =self.workspace4fit_.var("rrv_c_Exp%s%s_%s"%(label,mlvj_region,self.channel));
            rrv_delta_c = RooRealVar("rrv_delta_c_Exp%s%s_%s"%(label,mlvj_region,self.channel),"rrv_delta_c_Exp%s%s_%s"%(label,mlvj_region,self.channel),
                    self.workspace4fit_.var("rrv_c_Exp%s_signal_region_%s"%(label,self.channel)).getVal()-rrv_c_sb.getVal(),
                    self.workspace4fit_.var("rrv_c_Exp%s_signal_region_%s"%(label,self.channel)).getVal()-rrv_c_sb.getVal()-4*rrv_c_sb.getError(),
                    self.workspace4fit_.var("rrv_c_Exp%s_signal_region_%s"%(label,self.channel)).getVal()-rrv_c_sb.getVal()+4*rrv_c_sb.getError() )
            correct_factor_pdf = RooExponential("correct_factor_pdf","correct_factor_pdf",rrv_x,rrv_delta_c);

        elif mlvj_model=="2Exp":
            rrv_c0_sb     =self.workspace4fit_.var("rrv_c0_2Exp%s%s_%s"%(label,mlvj_region,self.channel));
            rrv_delta_c0 = RooRealVar("rrv_delta_c0_2Exp%s%s_%s"%(label,mlvj_region,self.channel),"rrv_delta_c0_2Exp%s%s_%s"%(label,mlvj_region,self.channel),
                    self.workspace4fit_.var("rrv_c0_2Exp%s_signal_region_%s"%(label,self.channel)).getVal()-rrv_c0_sb.getVal(),
                    self.workspace4fit_.var("rrv_c0_2Exp%s_signal_region_%s"%(label,self.channel)).getVal()-rrv_c0_sb.getVal()-4*rrv_c0_sb.getError(),
                    self.workspace4fit_.var("rrv_c0_2Exp%s_signal_region_%s"%(label,self.channel)).getVal()-rrv_c0_sb.getVal()+4*rrv_c0_sb.getError() )
            rrv_c0_sr =RooFormulaVar("rrv_c0_2Exp_sr%s%s_%s"%(label,mlvj_region,self.channel), "@0+@1",RooArgList(rrv_c0_sb, rrv_delta_c0 ) );
            rrv_c1_sb     =self.workspace4fit_.var("rrv_c1_2Exp%s%s_%s"%(label,mlvj_region,self.channel));
            rrv_delta_c1 = RooRealVar("rrv_delta_c1_2Exp%s%s_%s"%(label,mlvj_region,self.channel),"rrv_delta_c1_2Exp%s%s_%s"%(label,mlvj_region,self.channel),
                    self.workspace4fit_.var("rrv_c1_2Exp%s_signal_region_%s"%(label,self.channel)).getVal()-rrv_c1_sb.getVal(),
                    self.workspace4fit_.var("rrv_c1_2Exp%s_signal_region_%s"%(label,self.channel)).getVal()-rrv_c1_sb.getVal()-4*rrv_c1_sb.getError(),
                    self.workspace4fit_.var("rrv_c1_2Exp%s_signal_region_%s"%(label,self.channel)).getVal()-rrv_c1_sb.getVal()+4*rrv_c1_sb.getError() )
            rrv_c1_sr =RooFormulaVar("rrv_c1_2Exp_sr%s%s_%s"%(label,mlvj_region,self.channel), "@0+@1",RooArgList(rrv_c1_sb, rrv_delta_c1 ) ); 
            rrv_frac_sb     =self.workspace4fit_.var("rrv_frac_2Exp%s%s_%s"%(label,mlvj_region,self.channel));
            rrv_delta_frac = RooRealVar("rrv_delta_frac_2Exp%s%s_%s"%(label,mlvj_region,self.channel),"rrv_delta_frac_2Exp%s%s_%s"%(label,mlvj_region,self.channel),
                    self.workspace4fit_.var("rrv_frac_2Exp%s_signal_region_%s"%(label,self.channel)).getVal()-rrv_frac_sb.getVal(),
                    self.workspace4fit_.var("rrv_frac_2Exp%s_signal_region_%s"%(label,self.channel)).getVal()-rrv_frac_sb.getVal()-4*rrv_frac_sb.getError(),
                    self.workspace4fit_.var("rrv_frac_2Exp%s_signal_region_%s"%(label,self.channel)).getVal()-rrv_frac_sb.getVal()+4*rrv_frac_sb.getError() )
            rrv_frac_sr =RooFormulaVar("rrv_frac_2Exp_sr%s%s_%s"%(label,mlvj_region,self.channel), "@0+@1",RooArgList(rrv_frac_sb, rrv_delta_frac ) );

            correct_factor_pdf = RooAlpha42ExpPdf("correct_factor_pdf","correct_factor_pdf",rrv_x,rrv_c0_sr,rrv_c1_sr,rrv_frac_sr, rrv_c0_sb,rrv_c1_sb,rrv_frac_sb );

        elif mlvj_model=="Pow":
            rrv_c_sb     =self.workspace4fit_.var("rrv_c_Pow%s%s_%s"%(label,mlvj_region,self.channel));
            rrv_delta_c = RooRealVar("rrv_delta_c_Pow%s%s_%s"%(label,mlvj_region,self.channel),"rrv_delta_c_Pow%s%s_%s"%(label,mlvj_region,self.channel),0., -100*rrv_c_sb.getError(),100*rrv_c_sb.getError()); 
            correct_factor_pdf = RooPowPdf("correct_factor_pdf","correct_factor_pdf",rrv_x,rrv_delta_c);

        elif mlvj_model=="ExpN":
            rrv_c_sb     =self.workspace4fit_.var("rrv_c_ExpN%s%s_%s"%(label,mlvj_region,self.channel));
            rrv_n_sb     =self.workspace4fit_.var("rrv_n_ExpN%s%s_%s"%(label,mlvj_region,self.channel));
            rrv_delta_c = RooRealVar("rrv_delta_c_ExpN%s%s_%s"%(label,mlvj_region,self.channel),"rrv_delta_c_ExpN%s%s_%s"%(label,mlvj_region,self.channel),
                    self.workspace4fit_.var("rrv_c_ExpN%s_signal_region_%s"%(label,self.channel)).getVal()-rrv_c_sb.getVal(),
                    self.workspace4fit_.var("rrv_c_ExpN%s_signal_region_%s"%(label,self.channel)).getVal()-rrv_c_sb.getVal()-4*rrv_c_sb.getError(),
                    self.workspace4fit_.var("rrv_c_ExpN%s_signal_region_%s"%(label,self.channel)).getVal()-rrv_c_sb.getVal()+4*rrv_c_sb.getError() )
            rrv_delta_n = RooRealVar("rrv_delta_n_ExpN%s%s_%s"%(label,mlvj_region,self.channel),"rrv_delta_n_ExpN%s%s_%s"%(label,mlvj_region,self.channel),
                    self.workspace4fit_.var("rrv_n_ExpN%s_signal_region_%s"%(label,self.channel)).getVal()-rrv_n_sb.getVal(),
                    self.workspace4fit_.var("rrv_n_ExpN%s_signal_region_%s"%(label,self.channel)).getVal()-rrv_n_sb.getVal()-4*rrv_n_sb.getError(),
                    self.workspace4fit_.var("rrv_n_ExpN%s_signal_region_%s"%(label,self.channel)).getVal()-rrv_n_sb.getVal()+4*rrv_n_sb.getError() )
            rrv_c_sr =RooFormulaVar("rrv_c_ExpN_sr%s%s_%s"%(label,mlvj_region,self.channel), "@0+@1",RooArgList(rrv_c_sb, rrv_delta_c ) );
            rrv_n_sr =RooFormulaVar("rrv_n_ExpN_sr%s%s_%s"%(label,mlvj_region,self.channel), "@0+@1",RooArgList(rrv_n_sb, rrv_delta_n ) );
            #correct_factor_pdf = RooAlpha4ExpNPdf("correct_factor_pdf","correct_factor_pdf",rrv_x,rrv_c_sr, rrv_n_sr, rrv_c_sb, rrv_n_sb);
            correct_factor_pdf = RooExpNPdf("correct_factor_pdf","correct_factor_pdf",rrv_x,rrv_delta_c, rrv_delta_n);
 
        if mlvj_model=="ExpTail":

            rrv_s_sb     =self.workspace4fit_.var("rrv_s_ExpTail%s%s_%s"%(label,mlvj_region,self.channel));
            rrv_a_sb     =self.workspace4fit_.var("rrv_a_ExpTail%s%s_%s"%(label,mlvj_region,self.channel));
            rrv_delta_s = RooRealVar("rrv_delta_s_ExpTail%s%s_%s"%(label,mlvj_region,self.channel),"rrv_delta_s_ExpTail%s%s_%s"%(label,mlvj_region,self.channel),
                    self.workspace4fit_.var("rrv_s_ExpTail%s_signal_region_%s"%(label,self.channel)).getVal()-rrv_s_sb.getVal(),
                    self.workspace4fit_.var("rrv_s_ExpTail%s_signal_region_%s"%(label,self.channel)).getVal()-rrv_s_sb.getVal()-4*rrv_s_sb.getError(),
                    self.workspace4fit_.var("rrv_s_ExpTail%s_signal_region_%s"%(label,self.channel)).getVal()-rrv_s_sb.getVal()+4*rrv_s_sb.getError() )
            rrv_delta_a = RooRealVar("rrv_delta_a_ExpTail%s%s_%s"%(label,mlvj_region,self.channel),"rrv_delta_a_ExpTail%s%s_%s"%(label,mlvj_region,self.channel),
                    self.workspace4fit_.var("rrv_a_ExpTail%s_signal_region_%s"%(label,self.channel)).getVal()-rrv_a_sb.getVal(),
                    self.workspace4fit_.var("rrv_a_ExpTail%s_signal_region_%s"%(label,self.channel)).getVal()-rrv_a_sb.getVal()-4*rrv_a_sb.getError(),
                    self.workspace4fit_.var("rrv_a_ExpTail%s_signal_region_%s"%(label,self.channel)).getVal()-rrv_a_sb.getVal()+4*rrv_a_sb.getError() )
            rrv_s_sr =RooFormulaVar("rrv_s_ExpTail_sr%s%s_%s"%(label,mlvj_region,self.channel), "@0+@1",RooArgList(rrv_s_sb, rrv_delta_s ) );
            rrv_a_sr =RooFormulaVar("rrv_a_ExpTail_sr%s%s_%s"%(label,mlvj_region,self.channel), "@0+@1",RooArgList(rrv_a_sb, rrv_delta_a ) );

            correct_factor_pdf = RooAlpha4ExpTailPdf("correct_factor_pdf","correct_factor_pdf",rrv_x,rrv_s_sr, rrv_a_sr, rrv_s_sb, rrv_a_sb);
 
        if mlvj_model=="Pow2":

            rrv_c0_sb     =self.workspace4fit_.var("rrv_c0_Pow2%s%s_%s"%(label,mlvj_region,self.channel));
            rrv_c1_sb     =self.workspace4fit_.var("rrv_c1_Pow2%s%s_%s"%(label,mlvj_region,self.channel));
            rrv_delta_c0 = RooRealVar("rrv_delta_c0_Pow2%s%s_%s"%(label,mlvj_region,self.channel),"rrv_delta_c0_Pow2%s%s_%s"%(label,mlvj_region,self.channel),0., -100*rrv_c0_sb.getError(),100*rrv_c0_sb.getError()); 
            rrv_delta_c1 = RooRealVar("rrv_delta_c1_Pow2%s%s_%s"%(label,mlvj_region,self.channel),"rrv_delta_c1_Pow2%s%s_%s"%(label,mlvj_region,self.channel),0., -100*rrv_c1_sb.getError(),100*rrv_c1_sb.getError()); 
            correct_factor_pdf = RooPow2Pdf("correct_factor_pdf","correct_factor_pdf",rrv_x,rrv_delta_c0,rrv_delta_c1);

        model_pdf_sb_lo_WJets         = self.workspace4fit_.pdf("model_pdf%s%s_%s_mlvj"%(label,mlvj_region,self.channel));
        model_pdf_signal_region_WJets = RooProdPdf("model_pdf%s_signal_region_%s_mlvj"%(label,self.channel),"model_pdf%s_signal_region_%s_mlvj"%(label,self.channel) ,model_pdf_sb_lo_WJets,correct_factor_pdf);


        ### simultaneus fit to extract alpha

        data_category=RooCategory("data_category","data_category");
        data_category.defineType("sideband");
        data_category.defineType("signal_region");
        combData4fit=self.workspace4fit_.data("combData4fit%s%s_%s"%(label,mlvj_region,self.channel));

        simPdf=RooSimultaneous("simPdf","simPdf",data_category);
        simPdf.addPdf(model_pdf_sb_lo_WJets,"sideband");
        simPdf.addPdf(model_pdf_signal_region_WJets,"signal_region");

        rfresult=simPdf.fitTo(combData4fit,RooFit.Save(kTRUE), RooFit.SumW2Error(kTRUE));
        rfresult=simPdf.fitTo(combData4fit,RooFit.Save(kTRUE), RooFit.SumW2Error(kTRUE));
        rfresult.Print();
        rfresult.covarianceMatrix().Print(); #raw_input("ENTER");
        
        wsfit_tmp=RooWorkspace("wsfit_tmp%s%s_sim_mlvj"%(label,mlvj_region,));
        Deco=PdfDiagonalizer("Deco%s%s_sim_%s_%s_mlvj"%(label,mlvj_region,self.channel,self.wtagger_label),wsfit_tmp,rfresult);
        correct_factor_pdf_deco=Deco.diagonalize(correct_factor_pdf);
        correct_factor_pdf_deco.Print();
        correct_factor_pdf_deco.getParameters(rdataset_WJets_signal_region_mlvj).Print("v");
        getattr(self.workspace4fit_,"import")(correct_factor_pdf_deco);

        if label=="_WJets0":

            mplot_sb_lo = rrv_x.frame(RooFit.Title("WJets sb low"), RooFit.Bins(int(rrv_x.getBins()/self.narrow_factor)));
            rdataset_WJets_sb_lo_mlvj.plotOn(mplot_sb_lo, RooFit.MarkerSize(1.5), RooFit.DataError(RooAbsData.SumW2), RooFit.XErrorSize(0) );
            model_pdf_sb_lo_WJets.plotOn(mplot_sb_lo);
            mplot_pull_sideband=self.get_pull(rrv_x,mplot_sb_lo);
            parameters_list=model_pdf_sb_lo_WJets.getParameters(rdataset_WJets_sb_lo_mlvj);
            self.draw_canvas_with_pull( mplot_sb_lo, mplot_pull_sideband,parameters_list,"plots_%s_%s_%s_%s/other/"%(options.additioninformation, self.channel,self.PS_model,self.wtagger_label), "m_lvj%s_%s_sim"%(label,mlvj_region),"",1,0)

            mplot_signal_region = rrv_x.frame(RooFit.Title("WJets sr"), RooFit.Bins(int(rrv_x.getBins()/self.narrow_factor)));
            rdataset_WJets_signal_region_mlvj.plotOn(mplot_signal_region, RooFit.MarkerSize(1.5), RooFit.DataError(RooAbsData.SumW2), RooFit.XErrorSize(0) );
            model_pdf_signal_region_WJets.plotOn(mplot_signal_region);
            mplot_pull_signal_region=self.get_pull(rrv_x, mplot_signal_region);
            parameters_list=model_pdf_signal_region_WJets.getParameters(rdataset_WJets_signal_region_mlvj);
            self.draw_canvas_with_pull( mplot_signal_region, mplot_pull_signal_region,parameters_list,"plots_%s_%s_%s_%s/other/"%(options.additioninformation, self.channel,self.PS_model,self.wtagger_label), "m_lvj%s_signal_region_sim"%(label),"",1,0);

        model_pdf_sb_lo_WJets.plotOn(mplot,RooFit.Name("Sideband"),RooFit.LineStyle(10));
        model_pdf_signal_region_WJets.plotOn(mplot, RooFit.LineColor(kRed) ,RooFit.LineStyle(8), RooFit.Name("Signal Region"));
        correct_factor_pdf_deco.plotOn(mplot, RooFit.LineColor(kBlack),RooFit.Name("#alpha") );

        if label=="_WJets0":
            if self.workspace4fit_.pdf("correct_factor_pdf_Deco_WJets1%s_sim_%s_%s_mlvj"%(mlvj_region,self.channel,self.wtagger_label)):
                self.workspace4fit_.pdf("correct_factor_pdf_Deco_WJets1%s_sim_%s_%s_mlvj"%(mlvj_region,self.channel,self.wtagger_label)).plotOn(mplot, RooFit.LineColor(kMagenta), RooFit.LineStyle(3),RooFit.Name("#alpha: Alternate PS") ); 
            if self.workspace4fit_.pdf("correct_factor_pdf_Deco_WJets01%s_sim_%s_%s_mlvj"%(mlvj_region,self.channel,self.wtagger_label)):
                self.workspace4fit_.pdf("correct_factor_pdf_Deco_WJets01%s_sim_%s_%s_mlvj"%(mlvj_region,self.channel,self.wtagger_label)).plotOn(mplot, RooFit.LineColor(kOrange), RooFit.LineStyle(7),RooFit.Name("#alpha: Alternate Function") ); 

        paras=RooArgList();
        if mlvj_model=="ErfExp_v1" or mlvj_model=="ErfPow_v1"  or mlvj_model=="2Exp" :
            paras.add(self.workspace4fit_.var("Deco%s%s_sim_%s_%s_mlvj_eig0"%(label,mlvj_region,self.channel,self.wtagger_label) ));
            paras.add(self.workspace4fit_.var("Deco%s%s_sim_%s_%s_mlvj_eig1"%(label,mlvj_region,self.channel,self.wtagger_label) ));
            paras.add(self.workspace4fit_.var("Deco%s%s_sim_%s_%s_mlvj_eig2"%(label,mlvj_region,self.channel,self.wtagger_label) ));
            paras.add(self.workspace4fit_.var("Deco%s%s_sim_%s_%s_mlvj_eig3"%(label,mlvj_region,self.channel,self.wtagger_label) ));
            paras.add(self.workspace4fit_.var("Deco%s%s_sim_%s_%s_mlvj_eig4"%(label,mlvj_region,self.channel,self.wtagger_label) ));
            paras.add(self.workspace4fit_.var("Deco%s%s_sim_%s_%s_mlvj_eig5"%(label,mlvj_region,self.channel,self.wtagger_label) ));
        elif mlvj_model=="ErfPow2_v1" or mlvj_model=="ErfPowExp_v1" :
            paras.add(self.workspace4fit_.var("Deco%s%s_sim_%s_%s_mlvj_eig0"%(label,mlvj_region,self.channel,self.wtagger_label )));
            paras.add(self.workspace4fit_.var("Deco%s%s_sim_%s_%s_mlvj_eig1"%(label,mlvj_region,self.channel,self.wtagger_label )));
            paras.add(self.workspace4fit_.var("Deco%s%s_sim_%s_%s_mlvj_eig2"%(label,mlvj_region,self.channel,self.wtagger_label )));
            paras.add(self.workspace4fit_.var("Deco%s%s_sim_%s_%s_mlvj_eig3"%(label,mlvj_region,self.channel,self.wtagger_label )));
            paras.add(self.workspace4fit_.var("Deco%s%s_sim_%s_%s_mlvj_eig4"%(label,mlvj_region,self.channel,self.wtagger_label) ));
            paras.add(self.workspace4fit_.var("Deco%s%s_sim_%s_%s_mlvj_eig5"%(label,mlvj_region,self.channel,self.wtagger_label) ));
            paras.add(self.workspace4fit_.var("Deco%s%s_sim_%s_%s_mlvj_eig6"%(label,mlvj_region,self.channel,self.wtagger_label) ));
            paras.add(self.workspace4fit_.var("Deco%s%s_sim_%s_%s_mlvj_eig7"%(label,mlvj_region,self.channel,self.wtagger_label) ));
        elif mlvj_model=="Exp" or mlvj_model=="Pow":            
            paras.add(self.workspace4fit_.var("Deco%s%s_sim_%s_%s_mlvj_eig0"%(label,mlvj_region,self.channel,self.wtagger_label) ));
            paras.add(self.workspace4fit_.var("Deco%s%s_sim_%s_%s_mlvj_eig1"%(label,mlvj_region,self.channel,self.wtagger_label) ));
            
        elif mlvj_model=="ExpN" or mlvj_model=="ExpTail" or mlvj_model=="Pow2":
            paras.add(self.workspace4fit_.var("Deco%s%s_sim_%s_%s_mlvj_eig0"%(label,mlvj_region,self.channel,self.wtagger_label) ));
            paras.add(self.workspace4fit_.var("Deco%s%s_sim_%s_%s_mlvj_eig1"%(label,mlvj_region,self.channel,self.wtagger_label) ));
            paras.add(self.workspace4fit_.var("Deco%s%s_sim_%s_%s_mlvj_eig2"%(label,mlvj_region,self.channel,self.wtagger_label) ));
            paras.add(self.workspace4fit_.var("Deco%s%s_sim_%s_%s_mlvj_eig3"%(label,mlvj_region,self.channel,self.wtagger_label) ));

        if label=="_WJets0":
            draw_error_band_shape_Decor("correct_factor_pdf_Deco%s%s_sim_%s_%s_mlvj"%(label,mlvj_region,self.channel,self.wtagger_label),"rrv_mass_lvj", paras, self.workspace4fit_,1 ,mplot,kGray+3,"F",3001,"#alpha #pm",20,400);
            draw_error_band_shape_Decor("correct_factor_pdf_Deco%s%s_sim_%s_%s_mlvj"%(label,mlvj_region,self.channel,self.wtagger_label),"rrv_mass_lvj", paras, self.workspace4fit_,2 ,mplot,kGreen+2,"F",3002,"#alpha #pm",20,400);
            draw_error_band_shape_Decor("correct_factor_pdf_Deco%s%s_sim_%s_%s_mlvj"%(label,mlvj_region,self.channel,self.wtagger_label),"rrv_mass_lvj", paras, self.workspace4fit_,1 ,mplot,kGray+3,"F",3001,"#alpha_invisible #pm",20,400);

        correct_factor_pdf_deco.plotOn(mplot, RooFit.LineColor(kBlack),RooFit.Name("#alpha_invisible") );

        if label=="_WJets0":
            if self.workspace4fit_.pdf("correct_factor_pdf_Deco_WJets1%s_sim_%s_%s_mlvj"%(mlvj_region,self.channel,self.wtagger_label)):
                self.workspace4fit_.pdf("correct_factor_pdf_Deco_WJets1%s_sim_%s_%s_mlvj"%(mlvj_region,self.channel,self.wtagger_label)).plotOn(mplot, RooFit.LineColor(kMagenta), RooFit.LineStyle(3),RooFit.Name("#alpha_invisible: Alternate PS") ); 
            if self.workspace4fit_.pdf("correct_factor_pdf_Deco_WJets01%s_sim_%s_%s_mlvj"%(mlvj_region,self.channel,self.wtagger_label)):
                self.workspace4fit_.pdf("correct_factor_pdf_Deco_WJets01%s_sim_%s_%s_mlvj"%(mlvj_region,self.channel,self.wtagger_label)).plotOn(mplot, RooFit.LineColor(kOrange), RooFit.LineStyle(7),RooFit.Name("#alpha_invisible: Alternate Function") ); 

        leg=self.legend4Plot(mplot,-1,0, -0.15, 0);mplot.addObject(leg);

        if self.signal_sample=="ggH600" or self.signal_sample=="ggH700": tmp_y_max=0.25
        else: tmp_y_max=0.28
        mplot.GetYaxis().SetRangeUser(0,tmp_y_max);

        # pdf_sb, pdf_sr, pdf_alpha

        model_pdf_sb_lo_WJets.getVal(RooArgSet(rrv_x)),
        model_pdf_signal_region_WJets.getVal(RooArgSet(rrv_x)),
        correct_factor_pdf_deco.getVal(RooArgSet(rrv_x)),
        tmp_alpha_ratio=( model_pdf_signal_region_WJets.getVal(RooArgSet(rrv_x))/model_pdf_sb_lo_WJets.getVal(RooArgSet(rrv_x)) );
        tmp_alpha_pdf= correct_factor_pdf_deco.getVal(RooArgSet(rrv_x)) * mplot.getFitRangeBinW();
        tmp_alpha_scale=tmp_alpha_ratio/tmp_alpha_pdf;

        #add alpha scale axis
        axis_alpha=TGaxis( rrv_x.getMax(), 0, rrv_x.getMax(), tmp_y_max, 0, tmp_y_max*tmp_alpha_scale, 510, "+L");
        axis_alpha.SetTitle("#alpha");
        axis_alpha.SetTitleOffset(0.65);
        axis_alpha.SetTitleSize(0.05);
        axis_alpha.SetLabelSize(0.045);
        axis_alpha.SetTitleFont(42);
        axis_alpha.SetLabelFont(42);
        mplot.addObject(axis_alpha); 

        self.draw_canvas(mplot,"plots_%s_%s_%s_%s/other/"%(options.additioninformation, self.channel,self.PS_model,self.wtagger_label),"correction_pdf%s_%s_%s_%s_M_lvj_signal_region_to_sideband"%(label,self.PS_model,self.MODEL_4_mlvj,mlvj_region,),0,1);

        correct_factor_pdf_deco.getParameters(rdataset_WJets_sb_lo_mlvj).Print("v");

        model_pdf_WJets_sb_lo_from_fitting_mlvj_Deco=self.workspace4fit_.pdf("model_pdf%s%s_from_fitting_%s_mlvj_Deco%s%s_from_fitting_%s_%s_mlvj"%(label,mlvj_region,self.channel,label,mlvj_region, self.channel,self.wtagger_label));
        model_pdf_WJets_sb_lo_from_fitting_mlvj_Deco.Print("v");

        model_pdf_WJets_signal_region_after_correct_mlvj=RooProdPdf("model_pdf%s_signal_region_%s_after_correct_mlvj"%(label,self.channel),"model_pdf%s_signal_region_%s_after_correct_mlvj"%(label,self.channel),model_pdf_WJets_sb_lo_from_fitting_mlvj_Deco,self.workspace4fit_.pdf("correct_factor_pdf_Deco%s%s_sim_%s_%s_mlvj"%(label,mlvj_region,self.channel,self.wtagger_label)) );
        
        model_pdf_WJets_signal_region_after_correct_mlvj.Print()
        self.fix_Pdf(model_pdf_WJets_signal_region_after_correct_mlvj,RooArgSet(rrv_x))
        getattr(self.workspace4fit_,"import")(model_pdf_WJets_signal_region_after_correct_mlvj)

        #calculate the normalization and alpha for limit datacard
        self.workspace4fit_.var("rrv_number%s_signal_region_%s_mlvj"%(label,self.channel)).Print();
        self.workspace4fit_.var("rrv_number%s_in_mj_signal_region_from_fitting_%s"%(label,self.channel)).Print();
        self.workspace4fit_.var("rrv_number%s_signal_region_%s_mlvj"%(label,self.channel)).setVal(self.workspace4fit_.var("rrv_number%s_in_mj_signal_region_from_fitting_%s"%(label,self.channel)).getVal());
        self.workspace4fit_.var("rrv_number%s_signal_region_%s_mlvj"%(label,self.channel)).setError(self.workspace4fit_.var("rrv_number%s_in_mj_signal_region_from_fitting_%s"%(label,self.channel)).getError());

        self.workspace4fit_.var("rrv_number%s_signal_region_%s_mlvj"%(label,self.channel)).setConstant(kTRUE);

    ############# ---------------------------------------------------

    def fit_mj_single_MC(self,in_file_name, label, in_model_name, additioninformation=""):
        rrv_mass_j = self.workspace4fit_.var("rrv_mass_j"); 
        rdataset_mj = self.workspace4fit_.data("rdataset4fit"+label+"_"+self.channel+"_mj"); 
        rdataset_mj.Print();

        model = self.make_Model(label,in_model_name);
        rfresult = model.fitTo(rdataset_mj,RooFit.Save(1),RooFit.Extended(kTRUE) );
        rfresult = model.fitTo(rdataset_mj,RooFit.Save(1), RooFit.SumW2Error(kTRUE) ,RooFit.Extended(kTRUE) );
        rfresult = model.fitTo(rdataset_mj,RooFit.Save(1), RooFit.SumW2Error(kTRUE) ,RooFit.Extended(kTRUE) );

        mplot = rrv_mass_j.frame(RooFit.Title(label+" fitted by "+in_model_name), RooFit.Bins(int(rrv_mass_j.getBins()/self.narrow_factor)) );
        rdataset_mj.plotOn( mplot, RooFit.MarkerSize(1.5), RooFit.DataError(RooAbsData.SumW2), RooFit.XErrorSize(0) );
        draw_error_band_extendPdf(rdataset_mj, model, rfresult,mplot,6,"L");
        rdataset_mj.plotOn( mplot , RooFit.MarkerSize(1.5), RooFit.DataError(RooAbsData.SumW2), RooFit.XErrorSize(0) );
        model.plotOn( mplot , RooFit.VLines());
        model.plotOn( mplot );# remove RooFit.VLines()  in order to get right pull in the 1st bin 
        mplot_pull=self.get_pull(rrv_mass_j, mplot);
        parameters_list=model.getParameters(rdataset_mj);
        mplot.GetYaxis().SetRangeUser(1e-2,mplot.GetMaximum()*1.1);
        self.draw_canvas_with_pull( mplot, mplot_pull,parameters_list,"plots_%s_%s_%s_%s/m_j_fitting%s_wtaggercut%s_nPV%sto%s/"%(options.additioninformation, self.channel,self.PS_model, self.wtagger_label, additioninformation, self.wtagger_label, self.nPV_min, self.nPV_max), label+in_file_name, in_model_name)
        rfresult.Print(); 
        
        #normalize the number of total events to lumi
        self.workspace4fit_.var("rrv_number"+label+"_"+self.channel+"_mj").setVal( self.workspace4fit_.var("rrv_number"+label+"_"+self.channel+"_mj").getVal()*self.workspace4fit_.var("rrv_scale_to_lumi"+label+"_"+self.channel).getVal()  )
        self.workspace4fit_.var("rrv_number"+label+"_"+self.channel+"_mj").setError(self.workspace4fit_.var("rrv_number"+label+"_"+self.channel+"_mj").getError()*self.workspace4fit_.var("rrv_scale_to_lumi"+label+"_"+self.channel).getVal()  )
        if TString(label).Contains("ggH"):
            self.workspace4fit_.var("rrv_number"+label+"_"+self.channel+"_mj").setVal( self.workspace4fit_.var("rrv_number"+label+"_"+self.channel+"_mj").getVal()  )
            self.workspace4fit_.var("rrv_number"+label+"_"+self.channel+"_mj").setError(self.workspace4fit_.var("rrv_number"+label+"_"+self.channel+"_mj").getError() )
        self.workspace4fit_.var("rrv_number"+label+"_"+self.channel+"_mj").Print();

        #correct the mean and sigma from the ttbar contral sample
        par=parameters_list.createIterator();
        par.Reset();
        param=par.Next()
        while (param):
            if (TString(label).Contains("VV") or TString(label).Contains("STop") or TString(label).Contains("TTbar")):
                #param.Print();
                if TString(param.GetName()).Contains("rrv_mean1_gaus"):
                    param.setRange(param.getMin()+self.mean_shift, param.getMax()+self.mean_shift);
                    param.setVal(param.getVal()+self.mean_shift);
                    #param.Print(); raw_input("mean"+label);
                if TString(param.GetName()).Contains("rrv_deltamean_gaus"):
                    param.setRange(param.getMin()-self.mean_shift, param.getMax()-self.mean_shift);
                    param.setVal(param.getVal()-self.mean_shift);
                    #param.Print(); raw_input("mean"+label);
                if TString(param.GetName()).Contains("rrv_sigma1_gaus"):
                    param.setVal(param.getVal()*self.sigma_scale);
                    param.setRange(param.getMin()*self.sigma_scale, param.getMax()*self.sigma_scale);
                    #param.Print(); raw_input("sigma"+label);
                if TString(param.GetName()).Contains("rrv_scalesigma_gaus"):
                    param.setRange(param.getMin()/self.sigma_scale, param.getMax()/self.sigma_scale);
                    param.setVal(param.getVal()/self.sigma_scale);
                    #param.Print(); raw_input("sigma"+label);
            param=par.Next()
        #raw_input("over"+label);


    ############# ---------------------------------------------------
    def change_dataset_to_histpdf(self, x,dataset):
        datahist=dataset.binnedClone(dataset.GetName()+"_binnedClone",dataset.GetName()+"_binnedClone")
        histpdf=RooHistPdf(dataset.GetName()+"_histpdf",dataset.GetName()+"_histpdf",RooArgSet(x),datahist)
        getattr(self.workspace4fit_,"import")(histpdf)

    ############# ---------------------------------------------------
    def change_dataset_to_histogram(self, x,dataset,label=""):
        datahist=dataset.binnedClone(dataset.GetName()+"_binnedClone",dataset.GetName()+"_binnedClone")
        binswidth=5.;
        nbin=int( (x.getMax()-x.getMin())/binswidth );
        if label=="":
            return datahist.createHistogram("histo_%s"%(dataset.GetName()),x, RooFit.Binning( nbin ,x.getMin(),x.getMax()));
        else:
            return datahist.createHistogram("histo_"+label,x, RooFit.Binning( nbin,x.getMin(),x.getMax()));


    ########## ---------------------------------------------------
    def eventnumber_in_signalregion(self, label, model_ttbar_data, rfresult):# to get event number in mj signalregion
        rrv_mass_j = self.workspace4fit_.var("rrv_mass_j");
        rdataset_data_mj = self.workspace4fit_.data("rdataset"+label+"_"+self.channel+"_mj"); 

        rrv_number_ttbar_data=self.workspace4fit_.var("rrv_number_ttbar"+label+"_"+self.channel+"_mj");
        rrv_number_ttbar_data.Print();

        # to calculate the TTbar's normalization and error in M_J signal_region. The error must contain the shape error
        fullInt_data   = model_ttbar_data.createIntegral(RooArgSet(rrv_mass_j),RooArgSet(rrv_mass_j) );
        signalInt_data = model_ttbar_data.createIntegral(RooArgSet(rrv_mass_j),RooArgSet(rrv_mass_j),("signal_region"));
        fullInt_val_data=fullInt_data.getVal();
        signalInt_val_data=signalInt_data.getVal()/fullInt_val_data;
        rrv_number_TTbar_in_mj_signal_region_from_fitting=RooRealVar("rrv_number_ttbar_in_mj_signal_region_from_fitting"+label+"_"+self.channel,"rrv_number_ttbar_in_mj_signal_region_from_fitting"+label+"_"+self.channel,rrv_number_ttbar_data.getVal()*signalInt_val_data);
        #error
        rrv_number_TTbar_in_mj_signal_region_from_fitting.setError( Calc_error_extendPdf(rdataset_data_mj, model_ttbar_data, rfresult,"signal_region") );
        rrv_number_TTbar_in_mj_signal_region_from_fitting.Print();
        getattr(self.workspace4fit_,"import")(rrv_number_TTbar_in_mj_signal_region_from_fitting);



    ########## ---------------------------------------------------
    def get_mj_and_mlvj_dataset(self,in_file_name, label, jet_mass="jet_mass_pr"):# to get the shape of m_lvj

        # read in tree
        fileIn_name=TString(options.inPath+"/"+self.file_Directory+in_file_name);
        fileIn = TFile(fileIn_name.Data());
        treeIn = fileIn.Get("otree");
        
        rrv_mass_j = self.workspace4fit_.var("rrv_mass_j") 
        rrv_mass_lvj = self.workspace4fit_.var("rrv_mass_lvj") 
        rrv_weight = RooRealVar("rrv_weight","rrv_weight",0. ,10000000.) 

        #dataset of m_j

        rdataset_mj     = RooDataSet("rdataset"+label+"_"+self.channel+"_mj","rdataset"+label+"_"+self.channel+"_mj",RooArgSet(rrv_mass_j,rrv_weight),RooFit.WeightVar(rrv_weight) );
        rdataset4fit_mj = RooDataSet("rdataset4fit"+label+"_"+self.channel+"_mj","rdataset4fit"+label+"_"+self.channel+"_mj",RooArgSet(rrv_mass_j,rrv_weight),RooFit.WeightVar(rrv_weight) );

        #dataset of m_lvj

        rdataset_sb_lo_mlvj         = RooDataSet("rdataset"+label+"_sb_lo"+"_"+self.channel+"_mlvj","rdataset"+label+"_sb_lo"+"_"+self.channel+"_mlvj",RooArgSet(rrv_mass_lvj,rrv_weight),RooFit.WeightVar(rrv_weight) ); 
        rdataset_signal_region_mlvj = RooDataSet("rdataset"+label+"_signal_region"+"_"+self.channel+"_mlvj","rdataset"+label+"_signal_region"+"_"+self.channel+"_mlvj",RooArgSet(rrv_mass_lvj,rrv_weight),RooFit.WeightVar(rrv_weight) ); 
        rdataset_sb_hi_mlvj         = RooDataSet("rdataset"+label+"_sb_hi"+"_"+self.channel+"_mlvj","rdataset"+label+"_sb_hi"+"_"+self.channel+"_mlvj",RooArgSet(rrv_mass_lvj,rrv_weight),RooFit.WeightVar(rrv_weight) ); 

        rdataset4fit_sb_lo_mlvj     = RooDataSet("rdataset4fit"+label+"_sb_lo"+"_"+self.channel+"_mlvj","rdataset4fit"+label+"_sb_lo"+"_"+self.channel+"_mlvj",RooArgSet(rrv_mass_lvj,rrv_weight),RooFit.WeightVar(rrv_weight) ); 
        rdataset4fit_signal_region_mlvj = RooDataSet("rdataset4fit"+label+"_signal_region"+"_"+self.channel+"_mlvj","rdataset4fit"+label+"_signal_region"+"_"+self.channel+"_mlvj",RooArgSet(rrv_mass_lvj,rrv_weight),RooFit.WeightVar(rrv_weight) ); 
        rdataset4fit_sb_hi_mlvj     = RooDataSet("rdataset4fit"+label+"_sb_hi"+"_"+self.channel+"_mlvj","rdataset4fit"+label+"_sb_hi"+"_"+self.channel+"_mlvj",RooArgSet(rrv_mass_lvj,rrv_weight),RooFit.WeightVar(rrv_weight) ); 

        rdataset4fit_sb_lo_mlvj.Print();
        rdataset4fit_signal_region_mlvj.Print();
        data_category=RooCategory("data_category","data_category");
        data_category.defineType("sideband");
        data_category.defineType("signal_region");

        data_category2=RooCategory("data_category","data_category");
        data_category2.defineType("sideband");
        data_category2.defineType("signal_region");

        combData=RooDataSet("combData"+label+"_sb_lo"+"_"+self.channel,"combData"+label+"_sb_lo"+"_"+self.channel,RooArgSet(rrv_mass_lvj, data_category, rrv_weight),RooFit.WeightVar(rrv_weight) );
        combData2=RooDataSet("combData"+label+"_sb_hi"+"_"+self.channel,"combData"+label+"_sb_hi"+"_"+self.channel,RooArgSet(rrv_mass_lvj, data_category2, rrv_weight),RooFit.WeightVar(rrv_weight) );
        combData4fit=RooDataSet("combData4fit"+label+"_sb_lo"+"_"+self.channel,"combData4fit"+label+"_sb_lo"+"_"+self.channel,RooArgSet(rrv_mass_lvj, data_category, rrv_weight),RooFit.WeightVar(rrv_weight) );
        combData4fit2=RooDataSet("combData4fit"+label+"_sb_hi"+"_"+self.channel,"combData4fit"+label+"_sb_hi"+"_"+self.channel,RooArgSet(rrv_mass_lvj, data_category2, rrv_weight),RooFit.WeightVar(rrv_weight) );

        print "N entries: ", treeIn.GetEntries()

        hnum_4region=TH1D("hnum_4region"+label+"_"+self.channel,"hnum_4region"+label+"_"+self.channel,4,-1.5,2.5);# m_j   -1: sb_lo; 0:signal_region; 1: sb_hi; 2:total
        hnum_2region=TH1D("hnum_2region"+label+"_"+self.channel,"hnum_2region"+label+"_"+self.channel,2,-0.5,1.5);# m_lvj  0: signal_region; 1: total

        for i in range(treeIn.GetEntries()):
            if i % 100000 == 0: print "i: ",i
            treeIn.GetEntry(i);
            if i==0:
                tmp_scale_to_lumi=treeIn.wSampleWeight;
    
            discriminantCut = False; 

            wtagger=-1;
            wtagger=treeIn.jet_tau2tau1;
            if wtagger <self.wtagger_cut and wtagger > self.wtagger_cut_min :
                discriminantCut=True;
            else:
                discriminantCut=False;

            #jet mass, jet mass up, jet mass down
            tmp_jet_mass=getattr(treeIn, jet_mass);

            if treeIn.ungroomed_jet_pt > 200. and discriminantCut and tmp_jet_mass >= rrv_mass_j.getMin() and tmp_jet_mass<=rrv_mass_j.getMax() and treeIn.nbjets_csvm_veto < 1 and treeIn.mass_lvj >= rrv_mass_lvj.getMin() and treeIn.mass_lvj<=rrv_mass_lvj.getMax() and  treeIn.nPV >=self.nPV_min and treeIn.nPV<=self.nPV_max and treeIn.v_pt > self.vpt_cut and treeIn.pfMET > self.pfMET_cut and treeIn.l_pt > self.lpt_cut and treeIn.issignal==1:

                #print tmp_jet_mass_dn, tmp_jet_mass, tmp_jet_mass_up;
                tmp_event_weight= treeIn.totalEventWeight;
                tmp_event_weight4fit= treeIn.eff_and_pu_Weight;

                # for multi-sample, like STop and VV. There are two sample, and two wSampleWeight_value.Use the least wSampleWeight as scale. 
                tmp_event_weight4fit=tmp_event_weight4fit*treeIn.wSampleWeight/tmp_scale_to_lumi


                #wtagger_eff_reweight
                if not label=="_data": 
                    if TString(label).Contains("_TTbar") or TString(label).Contains("_STop") :
                        #print label+" SF %s"%(self.rrv_wtagger_eff_reweight_forT.getVal()) ;
                        tmp_event_weight=tmp_event_weight*self.rrv_wtagger_eff_reweight_forT.getVal();
                        tmp_event_weight4fit=tmp_event_weight4fit*self.rrv_wtagger_eff_reweight_forT.getVal();
                    else:
                        #print label+" SF %s"%(self.rrv_wtagger_eff_reweight_forV.getVal()) ;
                        tmp_event_weight=tmp_event_weight*self.rrv_wtagger_eff_reweight_forV.getVal();
                        tmp_event_weight4fit=tmp_event_weight4fit*self.rrv_wtagger_eff_reweight_forV.getVal();
                                             
                    tmp_event_weight=tmp_event_weight*treeIn.btag_weight;
                    tmp_event_weight4fit=tmp_event_weight4fit*treeIn.btag_weight;
                else:
                    tmp_event_weight=1.;
                    tmp_event_weight4fit=1
                
                rrv_mass_lvj.setVal(treeIn.mass_lvj);

                if tmp_jet_mass >= self.mj_sideband_lo_min and tmp_jet_mass < self.mj_sideband_lo_max:
                    rdataset_sb_lo_mlvj.add( RooArgSet( rrv_mass_lvj ), tmp_event_weight );
                    rdataset4fit_sb_lo_mlvj.add( RooArgSet( rrv_mass_lvj ), tmp_event_weight4fit );
                    data_category.setLabel("sideband"); 
                    combData.add(RooArgSet(rrv_mass_lvj,data_category),tmp_event_weight);
                    combData4fit.add(RooArgSet(rrv_mass_lvj,data_category),tmp_event_weight4fit);

                if tmp_jet_mass >= self.mj_signal_min      and tmp_jet_mass < self.mj_signal_max:
                    rdataset_signal_region_mlvj.add( RooArgSet( rrv_mass_lvj ), tmp_event_weight );
                    rdataset4fit_signal_region_mlvj.add( RooArgSet( rrv_mass_lvj ), tmp_event_weight4fit );
                    data_category.setLabel("signal_region");
                    data_category2.setLabel("signal_region");
                    combData.add(RooArgSet(rrv_mass_lvj,data_category),tmp_event_weight);
                    combData2.add(RooArgSet(rrv_mass_lvj,data_category2),tmp_event_weight);
                    combData4fit.add(RooArgSet(rrv_mass_lvj,data_category),tmp_event_weight4fit);
                    combData4fit2.add(RooArgSet(rrv_mass_lvj,data_category2),tmp_event_weight4fit);
                    hnum_2region.Fill(1,tmp_event_weight);

                if treeIn.mass_lvj >=self.mlvj_signal_min  and treeIn.mass_lvj <self.mlvj_signal_max: hnum_2region.Fill(0,tmp_event_weight);

                if tmp_jet_mass >= self.mj_sideband_hi_min and tmp_jet_mass < self.mj_sideband_hi_max:
                    rdataset_sb_hi_mlvj.add( RooArgSet( rrv_mass_lvj ), tmp_event_weight );
                    rdataset4fit_sb_hi_mlvj.add( RooArgSet( rrv_mass_lvj ), tmp_event_weight4fit );
                    data_category2.setLabel("sideband"); 
                    combData2.add(RooArgSet(rrv_mass_lvj,data_category2),tmp_event_weight);
                    combData4fit2.add(RooArgSet(rrv_mass_lvj,data_category2),tmp_event_weight4fit);

                rrv_mass_j.setVal( tmp_jet_mass );
                rdataset_mj.add( RooArgSet( rrv_mass_j ), tmp_event_weight );
                rdataset4fit_mj.add( RooArgSet( rrv_mass_j ), tmp_event_weight4fit );

                if tmp_jet_mass >=self.mj_sideband_lo_min and tmp_jet_mass <self.mj_sideband_lo_max: hnum_4region.Fill(-1,tmp_event_weight );
                if tmp_jet_mass >=self.mj_signal_min      and tmp_jet_mass <self.mj_signal_max     : hnum_4region.Fill(0,tmp_event_weight);
                if tmp_jet_mass >=self.mj_sideband_hi_min and tmp_jet_mass <self.mj_sideband_hi_max: hnum_4region.Fill(1,tmp_event_weight);
                hnum_4region.Fill(2,tmp_event_weight);

        if not label=="_data": 
            if TString(label).Contains("_TTbar") or TString(label).Contains("_STop") :
                tmp_scale_to_lumi=tmp_scale_to_lumi*self.rrv_wtagger_eff_reweight_forT.getVal();
            else:
                tmp_scale_to_lumi=tmp_scale_to_lumi*self.rrv_wtagger_eff_reweight_forV.getVal();
            tmp_scale_to_lumi=tmp_scale_to_lumi*treeIn.btag_weight;

        rrv_scale_to_lumi=RooRealVar("rrv_scale_to_lumi"+label+"_"+self.channel,"rrv_scale_to_lumi"+label+"_"+self.channel,tmp_scale_to_lumi)
        rrv_scale_to_lumi.Print()
        getattr(self.workspace4fit_,"import")(rrv_scale_to_lumi)

        #prepare m_lvj dataset
        rrv_number_dataset_signal_region_mlvj=RooRealVar("rrv_number_dataset_signal_region"+label+"_"+self.channel+"_mlvj","rrv_number_dataset_signal_region"+label+"_"+self.channel+"_mlvj",hnum_2region.GetBinContent(1));
        rrv_number_dataset_AllRange_mlvj=RooRealVar("rrv_number_dataset_AllRange"+label+"_"+self.channel+"_mlvj","rrv_number_dataset_AllRange"+label+"_"+self.channel+"_mlvj",hnum_2region.GetBinContent(2));
        getattr(self.workspace4fit_,"import")(rrv_number_dataset_signal_region_mlvj)
        getattr(self.workspace4fit_,"import")(rrv_number_dataset_AllRange_mlvj)
               
        getattr(self.workspace4fit_,"import")(rdataset_sb_lo_mlvj);
        getattr(self.workspace4fit_,"import")(rdataset_signal_region_mlvj);
        getattr(self.workspace4fit_,"import")(rdataset_sb_hi_mlvj); 
        getattr(self.workspace4fit_,"import")(rdataset4fit_sb_lo_mlvj);
        getattr(self.workspace4fit_,"import")(rdataset4fit_signal_region_mlvj);
        getattr(self.workspace4fit_,"import")(rdataset4fit_sb_hi_mlvj);
        getattr(self.workspace4fit_,"import")(combData);
        getattr(self.workspace4fit_,"import")(combData4fit);
        getattr(self.workspace4fit_,"import")(combData2);
        getattr(self.workspace4fit_,"import")(combData4fit2);
        self.file_out.write("\n%s events number in m_lvj from dataset: %s"%(label,rdataset_signal_region_mlvj.sumEntries()))

        #prepare m_j dataset
        rrv_number_dataset_sb_lo_mj=RooRealVar("rrv_number_dataset_sb_lo"+label+"_"+self.channel+"_mj","rrv_number_dataset_sb_lo"+label+"_"+self.channel+"_mj",hnum_4region.GetBinContent(1));
        rrv_number_dataset_signal_region_mj=RooRealVar("rrv_number_dataset_signal_region"+label+"_"+self.channel+"_mj","rrv_number_dataset_signal_region"+label+"_"+self.channel+"_mj",hnum_4region.GetBinContent(2));
        rrv_number_dataset_sb_hi_mj=RooRealVar("rrv_number_dataset_sb_hi"+label+"_"+self.channel+"_mj","rrv_number_dataset_sb_hi"+label+"_"+self.channel+"_mj",hnum_4region.GetBinContent(3));
        getattr(self.workspace4fit_,"import")(rrv_number_dataset_sb_lo_mj)
        getattr(self.workspace4fit_,"import")(rrv_number_dataset_signal_region_mj)
        getattr(self.workspace4fit_,"import")(rrv_number_dataset_sb_hi_mj)
                
        print "N_rdataset_mj: "
        getattr(self.workspace4fit_,"import")(rdataset_mj)
        getattr(self.workspace4fit_,"import")(rdataset4fit_mj)

        rdataset_sb_lo_mlvj.Print();
        rdataset_signal_region_mlvj.Print();
        rdataset_sb_hi_mlvj.Print();
        rdataset_mj.Print();
        rdataset4fit_sb_lo_mlvj.Print();
        rdataset4fit_signal_region_mlvj.Print();
        rdataset4fit_sb_hi_mlvj.Print();
        rdataset4fit_mj.Print();
        rrv_number_dataset_signal_region_mlvj.Print()
        rrv_number_dataset_AllRange_mlvj.Print()
        rrv_number_dataset_sb_lo_mj.Print()
        rrv_number_dataset_signal_region_mj.Print()
        rrv_number_dataset_sb_hi_mj.Print()
        print rdataset_signal_region_mlvj.sumEntries()
        print rrv_number_dataset_signal_region_mlvj.getVal()
        print rrv_number_dataset_AllRange_mlvj.getVal()
        #raw_input("ENTER");


    ######## ++++++++++++++
    def saveHist(self, label):
        rrv_mass_j = self.workspace4fit_.var("rrv_mass_j");
        rdataset_pass=self.workspace4fit_.data("rdataset"+label+"_"+self.channel+"_mj")
        rdataset_fail=self.workspace4fit_.data("rdataset"+label+"_failtau2tau1cut_"+self.channel+"_mj")
        hist_pass=self.change_dataset_to_histogram(rrv_mass_j,rdataset_pass,"pass"+label+"_"+self.channel);
        hist_fail=self.change_dataset_to_histogram(rrv_mass_j,rdataset_fail,"fail"+label+"_"+self.channel);
        #rootfile=TFile("histo_ttbarcontrolsample"+label+"_"+self.channel+".root","new");
        rootfile=TFile("histo_ttbarcontrolsample"+label+"_"+self.channel+".root","recreate");
        hist_pass.Write();
        hist_fail.Write();
        rootfile.Close();



    ######## ++++++++++++++
    def fit_mlvj_model_single_MC(self,in_file_name, label, in_range, mlvj_model, deco=0, show_constant_parameter=0, logy=0,ismc=0, is_hb=0):# model = shape + normalization

        rrv_mass_lvj = self.workspace4fit_.var("rrv_mass_lvj") 
        rdataset = self.workspace4fit_.data("rdataset4fit"+label+in_range+"_"+self.channel+"_mlvj");
        if is_hb !=0 :
         rdataset2 = self.workspace4fit_.data("rdataset4fit"+label+"_sb_hi"+"_"+self.channel+"_mlvj");
         rdataset.append(rdataset2);
         
        constrainslist =[];        
        model = self.make_Model(label+in_range,mlvj_model,"_mlvj",constrainslist,ismc);

        model.fitTo( rdataset, RooFit.Save(1), RooFit.SumW2Error(kTRUE) ,RooFit.Extended(kTRUE) );
        rfresult = model.fitTo( rdataset, RooFit.Save(1), RooFit.SumW2Error(kTRUE) ,RooFit.Extended(kTRUE) );
        rfresult.SetName("rfresult"+label+in_range+"_"+self.channel+"_mlvj")
        getattr(self.workspace4fit_,"import")(rfresult)
        
        mplot = rrv_mass_lvj.frame(RooFit.Title("M_{lvj"+in_range+"} fitted by "+mlvj_model), RooFit.Bins(int(rrv_mass_lvj.getBins()/self.narrow_factor)));
        rdataset.plotOn( mplot , RooFit.MarkerSize(1.5), RooFit.DataError(RooAbsData.SumW2), RooFit.XErrorSize(0)  );

        if not (TString(label).Contains("ggH") or  TString(label).Contains("vbfH") ): draw_error_band_extendPdf(rdataset, model, rfresult,mplot,6,"L")
        rdataset.plotOn( mplot , RooFit.MarkerSize(1.5), RooFit.DataError(RooAbsData.SumW2), RooFit.XErrorSize(0)  );
        model.plotOn( mplot , RooFit.VLines());
        model.plotOn( mplot ); 

        if deco :

            model_pdf=self.workspace4fit_.pdf("model_pdf%s%s_%s_mlvj"%(label,in_range,self.channel));
            model_pdf.fitTo( rdataset, RooFit.Save(1), RooFit.SumW2Error(kTRUE) );
            rfresult_pdf=model_pdf.fitTo( rdataset, RooFit.Save(1), RooFit.SumW2Error(kTRUE) );
            wsfit_tmp=RooWorkspace("wsfit_tmp"+label+in_range+"_"+self.channel+"_mlvj");
            Deco=PdfDiagonalizer("Deco"+label+in_range+"_"+self.channel+"_"+self.wtagger_label+"_mlvj",wsfit_tmp,rfresult_pdf);
            model_pdf_deco=Deco.diagonalize(model_pdf);
            getattr(self.workspace4fit_,"import")(model_pdf_deco);
            wsfit_tmp.Print("v");
            model_pdf_deco.getParameters(rdataset).Print("v");
            model_pdf.getParameters(rdataset).Print("v");
            model_pdf.Print();
            model_pdf_deco.Print();
            rfresult_pdf.covarianceMatrix().Print();# raw_input("ENTER");
            mplot_deco=rrv_mass_lvj.frame( RooFit.Bins(int(rrv_mass_lvj.getBins()/self.narrow_factor)));

            if label=="_TTbar" and in_range=="_signal_region": 
                rdataset.plotOn(mplot_deco, RooFit.Name("Powheg Sample"), RooFit.MarkerSize(1.5), RooFit.DataError(RooAbsData.SumW2), RooFit.XErrorSize(0) );
                model_pdf_deco.plotOn(mplot_deco,RooFit.Name("TTbar_Powheg"),RooFit.LineColor(kBlack));
                rrv_number_dataset=RooRealVar("rrv_number_dataset","rrv_number_dataset",rdataset.sumEntries());
                rrv_number_dataset.setError(0.)#(rdataset.sumEntries())**0.5);
                draw_error_band(rdataset, model_pdf,rrv_number_dataset,rfresult_pdf,mplot_deco,self.color_palet["Uncertainty"],"F");
                self.workspace4fit_.pdf("model_TTbar_MG_signal_region_%s_mlvj"%(self.channel)).plotOn(mplot_deco,RooFit.Name("TTbar_MG"), RooFit.LineStyle(kDashed),RooFit.LineColor(kBlack));
                self.workspace4fit_.pdf("model_TTbar_scaleUp_signal_region_%s_mlvj"%(self.channel)).plotOn(mplot_deco,RooFit.Name("TTbar_scaleUp"), RooFit.LineColor(kRed));
                self.workspace4fit_.pdf("model_TTbar_scaleDn_signal_region_%s_mlvj"%(self.channel)).plotOn(mplot_deco,RooFit.Name("TTbar_scaleDn"), RooFit.LineStyle(kDashed),RooFit.LineColor(kRed));
                self.workspace4fit_.pdf("model_TTbar_matchUp_signal_region_%s_mlvj"%(self.channel)).plotOn(mplot_deco,RooFit.Name("TTbar_matchUp"), RooFit.LineColor(kBlue));
                self.workspace4fit_.pdf("model_TTbar_matchDn_signal_region_%s_mlvj"%(self.channel)).plotOn(mplot_deco,RooFit.Name("TTbar_matchDn"), RooFit.LineStyle(kDashed),RooFit.LineColor(kBlue));
                self.workspace4fit_.var("rrv_number_TTbar_matchDn_signal_region_%s_mlvj"%(self.channel)).Print();
                self.workspace4fit_.var("rrv_number_TTbar_matchUp_signal_region_%s_mlvj"%(self.channel)).Print();
                self.workspace4fit_.var("rrv_number_TTbar_scaleDn_signal_region_%s_mlvj"%(self.channel)).Print();
                self.workspace4fit_.var("rrv_number_TTbar_scaleUp_signal_region_%s_mlvj"%(self.channel)).Print();
                self.workspace4fit_.var("rrv_number_TTbar_MG_signal_region_%s_mlvj"%(self.channel)).Print();
                self.workspace4fit_.var("rrv_number_TTbar_signal_region_%s_mlvj"%(self.channel)).Print();

            else:
                rdataset.plotOn(mplot_deco, RooFit.Name("Data"), RooFit.MarkerSize(1.5), RooFit.DataError(RooAbsData.SumW2), RooFit.XErrorSize(0) );
                model_pdf_deco.plotOn(mplot_deco,RooFit.Name(label),RooFit.LineColor(kBlack));
                rrv_number_dataset=RooRealVar("rrv_number_dataset","rrv_number_dataset",rdataset.sumEntries());
                rrv_number_dataset.setError(0.)#(rdataset.sumEntries())**0.5);
                draw_error_band(rdataset, model_pdf,rrv_number_dataset,rfresult_pdf,mplot_deco,self.color_palet["Uncertainty"],"F");

            leg=self.legend4Plot(mplot_deco,0);
            mplot_deco.addObject(leg);
            self.draw_canvas( mplot_deco, "plots_%s_%s_%s_%s/other/"%(options.additioninformation, self.channel,self.PS_model, self.wtagger_label), "m_lvj"+label+in_range+in_range+mlvj_model+"_deco",0,1)

        mplot_pull=self.get_pull(rrv_mass_lvj,mplot);
        parameters_list=model.getParameters(rdataset);
        mplot.GetYaxis().SetRangeUser(1e-2,mplot.GetMaximum()*1.1);
        self.draw_canvas_with_pull( mplot, mplot_pull,parameters_list,"plots_%s_%s_%s_%s/m_lvj_fitting/"%(options.additioninformation, self.channel,self.PS_model,self.wtagger_label), in_file_name,"m_lvj"+in_range+mlvj_model, show_constant_parameter, logy);
        #rfresult.Print(); rfresult.covarianceMatrix().Print(); raw_input("ENTER");

        #normalize the number of total events to lumi

        self.workspace4fit_.var("rrv_number"+label+in_range+"_"+self.channel+"_mlvj").Print();
        self.workspace4fit_.var("rrv_scale_to_lumi"+label+"_"+self.channel).Print()
        self.workspace4fit_.var("rrv_number"+label+in_range+"_"+self.channel+"_mlvj").setVal( self.workspace4fit_.var("rrv_number"+label+in_range+"_"+self.channel+"_mlvj").getVal()*self.workspace4fit_.var("rrv_scale_to_lumi"+label+"_"+self.channel).getVal()  )
        self.workspace4fit_.var("rrv_number"+label+in_range+"_"+self.channel+"_mlvj").setError(self.workspace4fit_.var("rrv_number"+label+in_range+"_"+self.channel+"_mlvj").getError()*self.workspace4fit_.var("rrv_scale_to_lumi"+label+"_"+self.channel).getVal()  )

        self.workspace4fit_.var("rrv_number"+label+in_range+"_"+self.channel+"_mlvj").Print(); #raw_input("ENTER");

    ######## ++++++++++++++
    def fit_WJetsNorm(self): # to  get the normalization of WJets in signal_region
        self.fit_WJetsNormalization_in_Mj_signal_region("_WJets0");
        self.fit_WJetsNormalization_in_Mj_signal_region("_WJets0massup","massup");
        self.fit_WJetsNormalization_in_Mj_signal_region("_WJets0massdn","massdn");
        self.fit_WJetsNormalization_in_Mj_signal_region("_WJets1");
        self.fit_WJetsNormalization_in_Mj_signal_region("_WJets01");

        rrv_WJets0=self.workspace4fit_.var("rrv_number_WJets0_in_mj_signal_region_from_fitting_%s"%(self.channel));
        rrv_WJets1=self.workspace4fit_.var("rrv_number_WJets1_in_mj_signal_region_from_fitting_%s"%(self.channel));
        rrv_WJets01=self.workspace4fit_.var("rrv_number_WJets01_in_mj_signal_region_from_fitting_%s"%(self.channel));
        rrv_WJets0massup=self.workspace4fit_.var("rrv_number_WJets0massup_in_mj_signal_region_from_fitting_%s"%(self.channel));
        rrv_WJets0massdn=self.workspace4fit_.var("rrv_number_WJets0massdn_in_mj_signal_region_from_fitting_%s"%(self.channel));

        rrv_WJets0.Print();
        rrv_WJets1.Print();
        rrv_WJets01.Print();
        total_uncertainty=TMath.Sqrt( TMath.Power(rrv_WJets0.getError(),2)+ TMath.Power(rrv_WJets1.getVal()-rrv_WJets0.getVal(),2)+ TMath.Power(rrv_WJets01.getVal()-rrv_WJets0.getVal(),2) );
        rrv_WJets0.setError(total_uncertainty);
        rrv_WJets0.Print();

        #jet mass uncertainty on WJets normalization
        if rrv_WJets0massdn and rrv_WJets0massdn:
            self.WJets_normlization_uncertainty_from_jet_mass= ( TMath.Abs(rrv_WJets0massup.getVal()-rrv_WJets0.getVal())+TMath.Abs(rrv_WJets0massdn.getVal()-rrv_WJets0.getVal() ) )/2./rrv_WJets0.getVal();  

        rrv_STop      =self.workspace4fit_.var("rrv_number_dataset_signal_region_STop_%s_mj"%(self.channel))
        rrv_STopmassup=self.workspace4fit_.var("rrv_number_dataset_signal_region_STopmassup_%s_mj"%(self.channel))
        rrv_STopmassdn=self.workspace4fit_.var("rrv_number_dataset_signal_region_STopmassdn_%s_mj"%(self.channel))
        self.STop_normlization_uncertainty_from_jet_mass=( TMath.Abs(rrv_STopmassup.getVal()-rrv_STop.getVal())+TMath.Abs(rrv_STopmassdn.getVal()-rrv_STop.getVal() ) )/2./rrv_STop.getVal();  

        rrv_TTbar      =self.workspace4fit_.var("rrv_number_dataset_signal_region_TTbar_%s_mj"%(self.channel))
        rrv_TTbarmassup=self.workspace4fit_.var("rrv_number_dataset_signal_region_TTbarmassup_%s_mj"%(self.channel))
        rrv_TTbarmassdn=self.workspace4fit_.var("rrv_number_dataset_signal_region_TTbarmassdn_%s_mj"%(self.channel))
        self.TTbar_normlization_uncertainty_from_jet_mass=( TMath.Abs(rrv_TTbarmassup.getVal()-rrv_TTbar.getVal())+TMath.Abs(rrv_TTbarmassdn.getVal()-rrv_TTbar.getVal() ) )/2./rrv_TTbar.getVal();  

        rrv_VV      =self.workspace4fit_.var("rrv_number_dataset_signal_region_VV_%s_mj"%(self.channel))
        rrv_VVmassup=self.workspace4fit_.var("rrv_number_dataset_signal_region_VVmassup_%s_mj"%(self.channel))
        rrv_VVmassdn=self.workspace4fit_.var("rrv_number_dataset_signal_region_VVmassdn_%s_mj"%(self.channel))
        self.VV_normlization_uncertainty_from_jet_mass=( TMath.Abs(rrv_VVmassup.getVal()-rrv_VV.getVal())+TMath.Abs(rrv_VVmassdn.getVal()-rrv_VV.getVal() ) )/2./rrv_VV.getVal();  

        #raw_input("ENTER");

    ######## ++++++++++++++
    def fit_WJetsNormalization_in_Mj_signal_region(self,label,massscale=""): # to  get the normalization of WJets in signal_region
        rrv_mass_j = self.workspace4fit_.var("rrv_mass_j") 
        #because the J_mass uncertainty only effect the shape, and the shape effect the WJets final normlization, so only use the rdataset_data_%s_mj, not use rdataset_datamassup rdataset_datamassdn
        rdataset_data_mj=self.workspace4fit_.data("rdataset_data_%s_mj"%(self.channel))

        model_TTbar=self.get_TTbar_mj_Model("_TTbar"+massscale);
        model_STop=self.get_STop_mj_Model("_STop"+massscale);
        model_VV=self.get_VV_mj_Model("_VV"+massscale);
        model_WJets=self.get_WJets_mj_Model(label);
        #model_TTbar.Print(); model_STop.Print(); model_VV.Print(); model_WJets.Print(); raw_input("ENTER");
        model_data=RooAddPdf("model_data%s_%s_mj"%(massscale,self.channel),"model_data%s_%s_mj"%(massscale,self.channel),RooArgList(model_WJets,model_VV,model_TTbar,model_STop));

        # fit the sideband range
        rfresult = model_data.fitTo( rdataset_data_mj, RooFit.Save(1) , RooFit.Range("sb_lo,sb_hi") ,RooFit.Extended(kTRUE), RooFit.NumCPU(2) );
        rfresult = model_data.fitTo( rdataset_data_mj, RooFit.Save(1) , RooFit.Range("sb_lo,sb_hi") ,RooFit.Extended(kTRUE), RooFit.NumCPU(2) );
        rfresult.Print(); rfresult.covarianceMatrix().Print();
        getattr(self.workspace4fit_,"import")(model_data);

        rrv_number_data_mj=RooRealVar("rrv_number_data%s_%s_mj"%(massscale,self.channel),"rrv_number_data%s_%s_mj"%(massscale,self.channel), 
                self.workspace4fit_.var("rrv_number_TTbar%s_%s_mj"%(massscale,self.channel)).getVal()+
                self.workspace4fit_.var("rrv_number_STop%s_%s_mj"%(massscale,self.channel)).getVal()+
                self.workspace4fit_.var("rrv_number_VV%s_%s_mj"%(massscale,self.channel)).getVal()+
                self.workspace4fit_.var("rrv_number%s_%s_mj"%(label,self.channel)).getVal()
                );
        rrv_number_data_mj.setError(TMath.Sqrt(
                self.workspace4fit_.var("rrv_number_TTbar%s_%s_mj"%(massscale,self.channel)).getError()*self.workspace4fit_.var("rrv_number_TTbar%s_%s_mj"%(massscale,self.channel)).getError()+
                self.workspace4fit_.var("rrv_number_STop%s_%s_mj"%(massscale,self.channel)).getError()*self.workspace4fit_.var("rrv_number_STop%s_%s_mj"%(massscale,self.channel)).getError()+
                self.workspace4fit_.var("rrv_number_VV%s_%s_mj"%(massscale,self.channel)).getError()*self.workspace4fit_.var("rrv_number_VV%s_%s_mj"%(massscale,self.channel)).getError()+
                self.workspace4fit_.var("rrv_number%s_%s_mj"%(label,self.channel)).getError()*self.workspace4fit_.var("rrv_number%s_%s_mj"%(label,self.channel)).getError()
                ));
        getattr(self.workspace4fit_,"import")(rrv_number_data_mj);
        scale_model_to_data=1;#rrv_number_data_mj.getVal()/rdataset_data_mj.sumEntries();
        
        if label=="_WJets0":
            mplot = rrv_mass_j.frame(RooFit.Title(""), RooFit.Bins(int(rrv_mass_j.getBins()/self.narrow_factor)));
            rdataset_data_mj.plotOn(mplot, RooFit.Name("data_invisible"), RooFit.MarkerSize(1.5), RooFit.DataError(RooAbsData.SumW2), RooFit.XErrorSize(0) );
    
            model_data.plotOn(mplot,RooFit.Name("VV"), RooFit.Components("model%s_%s_mj,model_STop_%s_mj,model_TTbar_%s_mj,model_VV_%s_mj"%(label,self.channel,self.channel,self.channel,self.channel)),RooFit.DrawOption("F"), RooFit.FillColor(self.color_palet["VV"]), RooFit.LineColor(kBlack),RooFit.NormRange("sb_lo,sb_hi"), RooFit.VLines());
            model_data.plotOn(mplot,RooFit.Name("TTbar"), RooFit.Components("model%s_%s_mj,model_STop_%s_mj,model_TTbar_%s_mj"%(label,self.channel,self.channel,self.channel)),RooFit.DrawOption("F"), RooFit.FillColor(self.color_palet["TTbar"]), RooFit.LineColor(kBlack),RooFit.NormRange("sb_lo,sb_hi"), RooFit.VLines());
            model_data.plotOn(mplot,RooFit.Name("STop"), RooFit.Components("model%s_%s_mj,model_STop_%s_mj"%(label,self.channel,self.channel)),RooFit.DrawOption("F"), RooFit.FillColor(self.color_palet["STop"]), RooFit.LineColor(kBlack),RooFit.NormRange("sb_lo,sb_hi"), RooFit.VLines());
            model_data.plotOn(mplot,RooFit.Name("WJets"), RooFit.Components("model%s_%s_mj"%(label,self.channel)),RooFit.DrawOption("F"), RooFit.FillColor(self.color_palet["WJets"]), RooFit.LineColor(kBlack),RooFit.NormRange("sb_lo,sb_hi"), RooFit.VLines());
    
            model_data.plotOn(mplot,RooFit.Name("VV_invisible"), RooFit.Components("model%s_%s_mj,model_STop_%s_mj,model_TTbar_%s_mj,model_VV_%s_mj"%(label,self.channel,self.channel,self.channel,self.channel)),RooFit.DrawOption("F"), RooFit.FillColor(self.color_palet["VV"]), RooFit.LineColor(kBlack),RooFit.FillStyle(3003),RooFit.Range(rrv_mass_j.getMin(),rrv_mass_j.getMax()),RooFit.NormRange("sb_lo,sb_hi"), RooFit.VLines());
            model_data.plotOn(mplot,RooFit.Name("TTbar_invisible"), RooFit.Components("model%s_%s_mj,model_STop_%s_mj,model_TTbar_%s_mj"%(label,self.channel,self.channel,self.channel)),RooFit.DrawOption("F"), RooFit.FillColor(self.color_palet["TTbar"]), RooFit.LineColor(kBlack),RooFit.FillStyle(3003),RooFit.Range(rrv_mass_j.getMin(),rrv_mass_j.getMax()),RooFit.NormRange("sb_lo,sb_hi"), RooFit.VLines());
            model_data.plotOn(mplot,RooFit.Name("STop_invisible"), RooFit.Components("model%s_%s_mj,model_STop_%s_mj"%(label,self.channel,self.channel)),RooFit.DrawOption("F"), RooFit.FillColor(self.color_palet["STop"]), RooFit.LineColor(kBlack),RooFit.FillStyle(3003),RooFit.Range(rrv_mass_j.getMin(),rrv_mass_j.getMax()),RooFit.NormRange("sb_lo,sb_hi"), RooFit.VLines());
            model_data.plotOn(mplot,RooFit.Name("WJets_invisible"), RooFit.Components("model%s_%s_mj"%(label,self.channel)),RooFit.DrawOption("F"), RooFit.FillColor(self.color_palet["WJets"]),RooFit.FillStyle(3003),RooFit.Range(rrv_mass_j.getMin(),rrv_mass_j.getMax()), RooFit.LineColor(kBlack),RooFit.NormRange("sb_lo,sb_hi"), RooFit.VLines());
    
            #solid line
            model_data.plotOn( mplot,RooFit.Name("_invisible"), RooFit.Components("model%s_%s_mj"%(label,self.channel)), RooFit.LineColor(kBlack), RooFit.LineWidth(2) ,RooFit.NormRange("sb_lo,sb_hi"), RooFit.VLines());
            model_data.plotOn( mplot,RooFit.Name("_invisible"), RooFit.Components("model%s_%s_mj,model_STop_%s_mj"%(label,self.channel,self.channel)), RooFit.LineColor(kBlack), RooFit.LineWidth(2),RooFit.NormRange("sb_lo,sb_hi"), RooFit.VLines());
            model_data.plotOn( mplot,RooFit.Name("_invisible"), RooFit.Components("model%s_%s_mj,model_STop_%s_mj,model_TTbar_%s_mj"%(label,self.channel,self.channel,self.channel)), RooFit.LineColor(kBlack), RooFit.LineWidth(2) ,RooFit.NormRange("sb_lo,sb_hi"), RooFit.VLines());
            model_data.plotOn( mplot,RooFit.Name("_invisible"), RooFit.Components("model%s_%s_mj,model_STop_%s_mj,model_TTbar_%s_mj,model_VV_%s_mj"%(label,self.channel,self.channel,self.channel,self.channel)),RooFit.LineColor(kBlack), RooFit.LineWidth(2) ,RooFit.NormRange("sb_lo,sb_hi"), RooFit.VLines());
            #dash line
            model_data.plotOn( mplot,RooFit.Name("_invisible"), RooFit.Components("model%s_%s_mj"%(label,self.channel)), RooFit.LineColor(kBlack), RooFit.LineWidth(2), RooFit.Range(rrv_mass_j.getMin(),rrv_mass_j.getMax()),RooFit.LineStyle(kDashed) ,RooFit.NormRange("sb_lo,sb_hi"), RooFit.VLines());
            model_data.plotOn( mplot,RooFit.Name("_invisible"), RooFit.Components("model%s_%s_mj,model_STop_%s_mj"%(label,self.channel,self.channel)), RooFit.LineColor(kBlack), RooFit.LineWidth(2), RooFit.Range(rrv_mass_j.getMin(),rrv_mass_j.getMax()),RooFit.LineStyle(kDashed) ,RooFit.NormRange("sb_lo,sb_hi"), RooFit.VLines());
            model_data.plotOn( mplot,RooFit.Name("_invisible"), RooFit.Components("model%s_%s_mj,model_STop_%s_mj,model_TTbar_%s_mj"%(label,self.channel,self.channel,self.channel)), RooFit.LineColor(kBlack), RooFit.LineWidth(2), RooFit.Range(rrv_mass_j.getMin(),rrv_mass_j.getMax()),RooFit.LineStyle(kDashed) ,RooFit.NormRange("sb_lo,sb_hi"), RooFit.VLines());
            model_data.plotOn( mplot,RooFit.Name("_invisible"), RooFit.Components("model%s_%s_mj,model_STop_%s_mj,model_TTbar_%s_mj,model_VV_%s_mj"%(label,self.channel,self.channel,self.channel,self.channel)),RooFit.LineColor(kBlack), RooFit.LineWidth(2), RooFit.Range(rrv_mass_j.getMin(),rrv_mass_j.getMax()),RooFit.LineStyle(kDashed) ,RooFit.NormRange("sb_lo,sb_hi"), RooFit.VLines());
            model_data.plotOn( mplot,RooFit.Name("_invisible"), RooFit.Components("model%s_%s_mj,model_STop_%s_mj,model_TTbar_%s_mj,model_VV_%s_mj"%(label,self.channel,self.channel,self.channel,self.channel)),RooFit.LineColor(kBlack), RooFit.LineWidth(2), RooFit.Range(rrv_mass_j.getMin(),rrv_mass_j.getMax()),RooFit.LineStyle(kDashed) ,RooFit.NormRange("sb_lo,sb_hi")); 
            rdataset_data_mj.plotOn(mplot, RooFit.Name("data"), RooFit.MarkerSize(1.5), RooFit.DataError(RooAbsData.SumW2), RooFit.XErrorSize(0) );
            draw_error_band(rdataset_data_mj, model_data, rrv_number_data_mj,rfresult,mplot,self.color_palet["Uncertainty"],"F");
            rdataset_data_mj.plotOn(mplot, RooFit.Name("data_invisible"), RooFit.MarkerSize(1.5), RooFit.DataError(RooAbsData.SumW2), RooFit.XErrorSize(0) );
            mplot_pull=self.get_pull(rrv_mass_j,mplot);

            #signal window
            lowerLine = TLine(self.mj_signal_min,0.,self.mj_signal_min,mplot.GetMaximum()); lowerLine.SetLineWidth(2); lowerLine.SetLineColor(kGray+2); lowerLine.SetLineStyle(9);
            upperLine = TLine(self.mj_signal_max,0.,self.mj_signal_max,mplot.GetMaximum()); upperLine.SetLineWidth(2); upperLine.SetLineColor(kGray+2); upperLine.SetLineStyle(9);
            mplot.addObject(lowerLine); mplot.addObject(upperLine);

            #legend
            leg=self.legend4Plot(mplot,0,1, 0.15, 0);
            mplot.addObject(leg);

            parameters_list=model_data.getParameters(rdataset_data_mj);
            mplot.GetYaxis().SetRangeUser(1e-2,mplot.GetMaximum()*1.5);
            self.draw_canvas_with_pull( mplot, mplot_pull,parameters_list,"plots_%s_%s_%s_%s/m_j_fitting_wtaggercut%s_nPV%sto%s/"%(options.additioninformation, self.channel,self.PS_model,self.wtagger_label, self.wtagger_label, self.nPV_min, self.nPV_max), "m_j_sideband%s"%(label),"",1)
    
            self.get_mj_normalization_insignalregion("_data");
            self.get_mj_normalization_insignalregion("_TTbar");
            self.get_mj_normalization_insignalregion("_STop");
            self.get_mj_normalization_insignalregion("_VV");
            self.get_mj_normalization_insignalregion(label);

        # to calculate the WJets's normalization and error in M_J signal_region. The error must contain the shape error
        fullInt   = model_WJets.createIntegral(RooArgSet(rrv_mass_j),RooArgSet(rrv_mass_j) );
        signalInt = model_WJets.createIntegral(RooArgSet(rrv_mass_j),RooArgSet(rrv_mass_j),("signal_region"));
        fullInt_val=fullInt.getVal()
        signalInt_val=signalInt.getVal()/fullInt_val
        rrv_number_WJets_in_mj_signal_region_from_fitting=RooRealVar("rrv_number%s_in_mj_signal_region_from_fitting_%s"%(label,self.channel),"rrv_number%s_in_mj_signal_region_from_fitting_%s"%(label,self.channel),self.workspace4fit_.var("rrv_number%s_%s_mj"%(label,self.channel)).getVal()*signalInt_val);

        #error
        rrv_number_WJets_in_mj_signal_region_from_fitting.setError( Calc_error_extendPdf(rdataset_data_mj, model_WJets, rfresult,"signal_region") );
        print "error=%s"%(rrv_number_WJets_in_mj_signal_region_from_fitting.getError());
        getattr(self.workspace4fit_,"import")(rrv_number_WJets_in_mj_signal_region_from_fitting);
        rrv_number_WJets_in_mj_signal_region_from_fitting.Print();

   ######## ++++++++++++++
    def fit_mlvj_in_Mj_sideband(self, label, mlvj_region, mlvj_model): 
        rrv_mass_j = self.workspace4fit_.var("rrv_mass_j") 
        rrv_mass_lvj = self.workspace4fit_.var("rrv_mass_lvj") 
        rdataset_data_mlvj=self.workspace4fit_.data("rdataset_data%s_%s_mlvj"%(mlvj_region,self.channel))

        model_VV_backgrounds    = self.get_VV_mlvj_Model(mlvj_region);    number_VV_sb_lo_mlvj   =self.workspace4fit_.var("rrv_number_VV%s_%s_mlvj"%(mlvj_region,self.channel))
        model_TTbar_backgrounds = self.get_TTbar_mlvj_Model(mlvj_region); number_TTbar_sb_lo_mlvj=self.workspace4fit_.var("rrv_number_TTbar%s_%s_mlvj"%(mlvj_region,self.channel))
        model_STop_backgrounds  = self.get_STop_mlvj_Model(mlvj_region);  number_STop_sb_lo_mlvj =self.workspace4fit_.var("rrv_number_STop%s_%s_mlvj"%(mlvj_region,self.channel))

        model_pdf_WJets = self.make_Pdf("%s%s_from_fitting"%(label,mlvj_region), mlvj_model,"_mlvj");
        model_pdf_WJets.Print();
        number_WJets_sb_lo=self.workspace4fit_.var("rrv_number%s%s_%s_mlvj"%(label,mlvj_region,self.channel)).clone("rrv_number%s%s_from_fitting_%s_mlvj"%(label,mlvj_region,self.channel));
        model_WJets=RooExtendPdf("model%s%s_from_fitting_%s_mlvj"%(label,mlvj_region,self.channel),"model%s%s_from_fitting_%s_mlvj"%(label,mlvj_region,self.channel),model_pdf_WJets,number_WJets_sb_lo);
        model_pdf_WJets.Print(); number_WJets_sb_lo.Print()

        model_data=RooAddPdf("model_data%s%s_mlvj"%(label,mlvj_region),"model_data%s%s_mlvj"%(label,mlvj_region),RooArgList(model_WJets,model_VV_backgrounds, model_TTbar_backgrounds, model_STop_backgrounds));
        rfresult = model_data.fitTo( rdataset_data_mlvj, RooFit.Save(1) ,RooFit.Extended(kTRUE));
        rfresult = model_data.fitTo( rdataset_data_mlvj, RooFit.Save(1) ,RooFit.Extended(kTRUE));
        rfresult.Print();
        rfresult.covarianceMatrix().Print(); 
        getattr(self.workspace4fit_,"import")(model_data)

        self.workspace4fit_.var("rrv_number_TTbar%s_%s_mlvj"%(mlvj_region,self.channel)).Print();
        self.workspace4fit_.var("rrv_number_STop%s_%s_mlvj"%(mlvj_region,self.channel)).Print();
        self.workspace4fit_.var("rrv_number_VV%s_%s_mlvj"%(mlvj_region,self.channel)).Print();
        self.workspace4fit_.var("rrv_number%s%s_from_fitting_%s_mlvj"%(label,mlvj_region,self.channel)).Print();

        rrv_number_data_sb_lo_mlvj=RooRealVar("rrv_number_data%s_%s_mlvj"%(mlvj_region,self.channel),"rrv_number_data%s_%s_mlvj"%(mlvj_region,self.channel), self.workspace4fit_.var("rrv_number_TTbar%s_%s_mlvj"%(mlvj_region,self.channel)).getVal()+self.workspace4fit_.var("rrv_number_STop%s_%s_mlvj"%(mlvj_region,self.channel)).getVal()+self.workspace4fit_.var("rrv_number_VV%s_%s_mlvj"%(mlvj_region,self.channel)).getVal()+self.workspace4fit_.var("rrv_number%s%s_from_fitting_%s_mlvj"%(label,mlvj_region,self.channel)).getVal() );

        rrv_number_data_sb_lo_mlvj.setError( TMath.Sqrt(
            self.workspace4fit_.var("rrv_number%s%s_from_fitting_%s_mlvj"%(label,mlvj_region,self.channel)).getError()*self.workspace4fit_.var("rrv_number%s%s_from_fitting_%s_mlvj"%(label,mlvj_region,self.channel)).getError() ) );

        rrv_number_data_sb_lo_mlvj.setError(0.);#we only care about the M_lvj shape uncertainty
        getattr(self.workspace4fit_,"import")(rrv_number_data_sb_lo_mlvj)
        #rdataset_data_mlvj.Print(); #rrv_number_data_sb_lo_mlvj.Print();# raw_input("ENTER");

        model_WJets.Print();
        model_WJets.getParameters(rdataset_data_mlvj).Print("v");
        self.workspace4fit_.pdf("model_pdf%s%s_%s_mlvj"%(label,mlvj_region,self.channel)).getParameters(rdataset_data_mlvj).Print("v");
        #raw_input("ENTER");

        if label=="_WJets0":
            mplot = rrv_mass_lvj.frame(RooFit.Title("M_lvj fitted in M_j sideband "), RooFit.Bins(int(rrv_mass_lvj.getBins()/self.narrow_factor)));
            rdataset_data_mlvj.plotOn( mplot , RooFit.Invisible(), RooFit.MarkerSize(1.5), RooFit.DataError(RooAbsData.SumW2), RooFit.XErrorSize(0) );
            model_data.plotOn(mplot, RooFit.Components("model%s%s_from_fitting_%s_mlvj,model_TTbar%s_%s_mlvj,model_STop%s_%s_mlvj,model_VV%s_%s_mlvj"%(label,mlvj_region,self.channel,mlvj_region,self.channel,mlvj_region,self.channel,mlvj_region,self.channel)), RooFit.Name("WJets"),RooFit.DrawOption("F"), RooFit.FillColor(self.color_palet["WJets"]), RooFit.LineColor(kBlack), RooFit.VLines()) ;
            model_data.plotOn(mplot, RooFit.Components("model_TTbar%s_%s_mlvj,model_STop%s_%s_mlvj,model_VV%s_%s_mlvj"%(mlvj_region,self.channel,mlvj_region,self.channel,mlvj_region,self.channel)),RooFit.Name("VV"),RooFit.DrawOption("F"), RooFit.FillColor(self.color_palet["VV"]), RooFit.LineColor(kBlack), RooFit.VLines()) ;
            model_data.plotOn(mplot, RooFit.Components("model_TTbar%s_%s_mlvj,model_STop%s_%s_mlvj"%(mlvj_region,self.channel,mlvj_region,self.channel)), RooFit.Name("TTbar"),RooFit.DrawOption("F"), RooFit.FillColor(self.color_palet["TTbar"]), RooFit.LineColor(kBlack), RooFit.VLines());
            model_data.plotOn(mplot, RooFit.Components("model_STop%s_%s_mlvj"%(mlvj_region,self.channel)), RooFit.Name("STop"), RooFit.DrawOption("F"), RooFit.FillColor(self.color_palet["STop"]), RooFit.LineColor(kBlack), RooFit.VLines());
            #solid line
            model_data.plotOn(mplot, RooFit.Components("model%s%s_from_fitting_%s_mlvj,model_TTbar%s_%s_mlvj,model_STop%s_%s_mlvj,model_VV%s_%s_mlvj"%(label,mlvj_region,self.channel,mlvj_region,self.channel,mlvj_region,self.channel,mlvj_region,self.channel)), RooFit.Name("WJets_line_invisible"), RooFit.LineColor(kBlack), RooFit.LineWidth(2), RooFit.VLines()) ;
            model_data.plotOn(mplot, RooFit.Components("model_TTbar%s_%s_mlvj,model_STop%s_%s_mlvj,model_VV%s_%s_mlvj"%(mlvj_region,self.channel,mlvj_region,self.channel,mlvj_region,self.channel)),RooFit.Name("VV_line_invisible"), RooFit.LineColor(kBlack), RooFit.LineWidth(2), RooFit.VLines()) ;
            model_data.plotOn(mplot, RooFit.Components("model_TTbar%s_%s_mlvj,model_STop%s_%s_mlvj"%(mlvj_region,self.channel,mlvj_region,self.channel)), RooFit.Name("TTbar_line_invisible"), RooFit.LineColor(kBlack), RooFit.LineWidth(2), RooFit.VLines());
            model_data.plotOn(mplot, RooFit.Components("model_STop%s_%s_mlvj"%(mlvj_region,self.channel)), RooFit.Name("STop_line_invisible"), RooFit.LineColor(kBlack), RooFit.LineWidth(2), RooFit.VLines());
 

            rdataset_data_mlvj.plotOn(mplot,RooFit.Name("data"), RooFit.MarkerSize(1.5), RooFit.DataError(RooAbsData.SumW2), RooFit.XErrorSize(0) );
            draw_error_band(rdataset_data_mlvj, model_data,self.workspace4fit_.var("rrv_number_data%s_%s_mlvj"%(mlvj_region,self.channel)) ,rfresult,mplot,self.color_palet["Uncertainty"],"F");
            model_data.plotOn( mplot , RooFit.VLines(), RooFit.Invisible());
            model_data.plotOn( mplot , RooFit.Invisible());
            rdataset_data_mlvj.plotOn(mplot,RooFit.Name("data_invisible1"), RooFit.MarkerSize(1.5), RooFit.DataError(RooAbsData.SumW2), RooFit.XErrorSize(0) );

            leg=self.legend4Plot(mplot,0,1,0.1 );#add legend
            mplot.addObject(leg)

            #chi2
            self.nPar_float_in_fitTo=rfresult.floatParsFinal().getSize();
            
            nBinX=mplot.GetNbinsX();
            ndof= nBinX-self.nPar_float_in_fitTo;
            print mplot.chiSquare();
            print "nPar=%s,  chiSquare=%s/%s"%(self.nPar_float_in_fitTo ,mplot.chiSquare(self.nPar_float_in_fitTo)*ndof, ndof ); #raw_input("ENTER");
            self.file_out.write("\n fit_mlvj_in_Mj_sideband: nPar=%s, chiSquare=%s/%s"%(self.nPar_float_in_fitTo, mplot.chiSquare( self.nPar_float_in_fitTo )*ndof, ndof ) );
    
            mplot_pull=self.get_pull(rrv_mass_lvj,mplot);
            parameters_list=model_data.getParameters(rdataset_data_mlvj);
            mplot.GetYaxis().SetRangeUser(1e-2,mplot.GetMaximum()*1.5);
            self.draw_canvas_with_pull( mplot, mplot_pull,parameters_list,"plots_%s_%s_%s_%s/m_lvj_fitting/"%(options.additioninformation, self.channel,self.PS_model,self.wtagger_label), "m_lvj%s_%s"%(mlvj_region,label),"",1,1)

        #model deco
        wsfit_tmp=RooWorkspace("wsfit_tmp%s%s_from_fitting_mlvj"%(mlvj_region,label));
        Deco=PdfDiagonalizer("Deco%s%s_from_fitting_%s_%s_mlvj"%(label,mlvj_region,self.channel,self.wtagger_label),wsfit_tmp,rfresult);
        model_pdf_WJets_deco=Deco.diagonalize(model_pdf_WJets); model_pdf_WJets_deco.Print("v");
        model_pdf_WJets_deco.getParameters(rdataset_data_mlvj).Print("") ;wsfit_tmp.allVars().Print("v");
        getattr(self.workspace4fit_,"import")(model_pdf_WJets_deco);

        self.get_WJets_mlvj_correction_sb_lo_to_signal_region(label,mlvj_region,mlvj_model);

        self.fix_Model("_%s"%(self.signal_sample),"_signal_region","_mlvj")
        self.fix_Model("_TTbar","_signal_region","_mlvj")
        self.fix_Model("_STop","_signal_region","_mlvj")
        self.fix_Model("_VV","_signal_region","_mlvj")

        self.get_mlvj_normalization_insignalregion("_%s"%(self.signal_sample));

        self.get_mlvj_normalization_insignalregion("_TTbar");
        self.get_mlvj_normalization_insignalregion("_STop");
        self.get_mlvj_normalization_insignalregion("_VV");
        self.get_mlvj_normalization_insignalregion(label,"model_pdf%s_signal_region_%s_after_correct_mlvj"%(label,self.channel));

   ######## ++++++++++++++
    def fit_mlvj_in_Mj_signalregion(self, label, mlvj_region, mlvj_model):  #mlvj_model="_signal_region"
        parameters_workspace=self.workspace4fit_.allVars();
        par=parameters_workspace.createIterator();
        par.Reset();
        param=par.Next()
        while (param):
            param.Print();
            param=par.Next()
        print "___________________________________________________"
        pdfs_workspace=self.workspace4fit_.allPdfs();
        par=pdfs_workspace.createIterator();
        par.Reset();
        param=par.Next()
        while (param):
            param.Print();
            param=par.Next()
        print "___________________________________________________"


        rrv_mass_lvj = self.workspace4fit_.var("rrv_mass_lvj") 
        rdataset_data_mlvj=self.workspace4fit_.data("rdataset_data%s_%s_mlvj"%(mlvj_region,self.channel))

        number_WJets0_signal_region_mlvj =self.workspace4fit_.var("rrv_number_WJets0_signal_region_%s_mlvj"%(self.channel))
        number_TTbar_signal_region_mlvj  =self.workspace4fit_.var("rrv_number_TTbar_signal_region_%s_mlvj"%(self.channel))
        number_VV_signal_region_mlvj     =self.workspace4fit_.var("rrv_number_VV_signal_region_%s_mlvj"%(self.channel))
        number_STop_signal_region_mlvj   =self.workspace4fit_.var("rrv_number_STop_signal_region_%s_mlvj"%(self.channel))

        number_WJets0_signal_region_mlvj.setConstant(0) 
        number_TTbar_signal_region_mlvj.setConstant(0) 
        number_VV_signal_region_mlvj.setConstant(0)    
        number_STop_signal_region_mlvj.setConstant(0)  

        number_TTbar_signal_region_mlvj.setError( TMath.Sqrt(  number_TTbar_signal_region_mlvj.getError()*number_TTbar_signal_region_mlvj.getError() + number_TTbar_signal_region_mlvj.getVal()*self.XS_TTbar_NLO_uncertainty*number_TTbar_signal_region_mlvj.getVal()*self.XS_TTbar_NLO_uncertainty )  )
        number_STop_signal_region_mlvj.setError( TMath.Sqrt(  number_STop_signal_region_mlvj.getError()*number_STop_signal_region_mlvj.getError() + number_STop_signal_region_mlvj.getVal()*self.XS_STop_NLO_uncertainty*number_STop_signal_region_mlvj.getVal()*self.XS_STop_NLO_uncertainty )  )
        number_VV_signal_region_mlvj.setError( TMath.Sqrt(  number_VV_signal_region_mlvj.getError()*number_VV_signal_region_mlvj.getError() + number_VV_signal_region_mlvj.getVal()*self.XS_VV_NLO_uncertainty*number_VV_signal_region_mlvj.getVal()*self.XS_VV_NLO_uncertainty )  )

        number_ConstraintsList=[];
        self.addConstraint(number_WJets0_signal_region_mlvj, number_WJets0_signal_region_mlvj.getVal(), number_WJets0_signal_region_mlvj.getError(), number_ConstraintsList);
        self.addConstraint(number_TTbar_signal_region_mlvj, number_TTbar_signal_region_mlvj.getVal(), number_TTbar_signal_region_mlvj.getError(), number_ConstraintsList);
        self.addConstraint(number_VV_signal_region_mlvj, number_VV_signal_region_mlvj.getVal(), number_VV_signal_region_mlvj.getError(), number_ConstraintsList);
        self.addConstraint(number_STop_signal_region_mlvj, number_STop_signal_region_mlvj.getVal(), number_STop_signal_region_mlvj.getError(), number_ConstraintsList);
 
        number_WJets0_signal_region_mlvj.Print()
        number_TTbar_signal_region_mlvj.Print() 
        number_VV_signal_region_mlvj.Print()    
        number_STop_signal_region_mlvj.Print()  
        #raw_input("ENTER");

        pdfconstrainslist=RooArgSet("pdfconstrainslist");
        for i in range(len(number_ConstraintsList)):
            self.workspace4fit_.pdf(number_ConstraintsList[i]).Print();
            pdfconstrainslist.add(self.workspace4fit_.pdf(number_ConstraintsList[i]) );
        pdfconstrainslist.Print();


        model_pdf_WJets0_backgrounds  = self.workspace4fit_.pdf("model_pdf_WJets0_signal_region_%s_after_correct_mlvj"%(self.channel)) 
        model_pdf_TTbar_backgrounds   = self.workspace4fit_.pdf("model_pdf_TTbar_signal_region_%s_mlvj_Deco_TTbar_signal_region_%s_%s_mlvj"%(self.channel, self.channel, self.wtagger_label)) 
        model_pdf_VV_backgrounds      = self.workspace4fit_.pdf("model_pdf_VV_signal_region_%s_mlvj"%(self.channel))  
        model_pdf_STop_backgrounds    = self.workspace4fit_.pdf("model_pdf_STop_signal_region_%s_mlvj"%(self.channel)) 

        self.fix_Pdf(model_pdf_WJets0_backgrounds, RooArgSet(rrv_mass_lvj) );
        self.fix_Pdf(model_pdf_TTbar_backgrounds,  RooArgSet(rrv_mass_lvj) );
        self.fix_Pdf(model_pdf_VV_backgrounds,     RooArgSet(rrv_mass_lvj) );
        self.fix_Pdf(model_pdf_STop_backgrounds,   RooArgSet(rrv_mass_lvj) );

        model_data=RooAddPdf("model_data%s%s_mlvj"%(label,mlvj_region),"model_data%s%s_mlvj"%(label,mlvj_region),RooArgList(model_pdf_WJets0_backgrounds, model_pdf_TTbar_backgrounds, model_pdf_VV_backgrounds, model_pdf_STop_backgrounds), RooArgList(number_WJets0_signal_region_mlvj, number_TTbar_signal_region_mlvj, number_VV_signal_region_mlvj, number_STop_signal_region_mlvj) );
        rfresult = model_data.fitTo( rdataset_data_mlvj, RooFit.Save(1) ,RooFit.Extended(kTRUE) ,RooFit.ExternalConstraints(pdfconstrainslist) );
        rfresult = model_data.fitTo( rdataset_data_mlvj, RooFit.Save(1) ,RooFit.Extended(kTRUE) ,RooFit.ExternalConstraints(pdfconstrainslist) );
        rfresult.Print();
        rfresult.covarianceMatrix().Print(); #raw_input("ENTER");
        getattr(self.workspace4fit_,"import")(model_data)
        
        self.fix_Model("_%s"%(self.signal_sample),"_signal_region","_mlvj")
        self.fix_Model("_TTbar","_signal_region","_mlvj")
        self.fix_Model("_STop","_signal_region","_mlvj")
        self.fix_Model("_VV","_signal_region","_mlvj")

        self.get_mlvj_normalization_insignalregion("_%s"%(self.signal_sample));
        self.get_mlvj_normalization_insignalregion("_TTbar");
        self.get_mlvj_normalization_insignalregion("_STop");
        self.get_mlvj_normalization_insignalregion("_VV");
        self.get_mlvj_normalization_insignalregion(label,"model_pdf%s_signal_region_%s_after_correct_mlvj"%(label,self.channel));

    ######## ++++++++++++++
    def get_mj_normalization_insignalregion(self, label):
        print "get mj normalization "+ label
        model = self.workspace4fit_.pdf("model"+label+"_"+self.channel+"_mj");
        rrv_mass_j = self.workspace4fit_.var("rrv_mass_j");

        fullInt   = model.createIntegral(RooArgSet(rrv_mass_j),RooArgSet(rrv_mass_j) );
        sb_loInt   = model.createIntegral(RooArgSet(rrv_mass_j),RooArgSet(rrv_mass_j),("sb_lo"));
        signalInt = model.createIntegral(RooArgSet(rrv_mass_j),RooArgSet(rrv_mass_j),("signal_region"));
        sb_hiInt   = model.createIntegral(RooArgSet(rrv_mass_j),RooArgSet(rrv_mass_j),("sb_hi"));
        
        fullInt_val=fullInt.getVal()
        sb_loInt_val=sb_loInt.getVal()/fullInt_val
        sb_hiInt_val=sb_hiInt.getVal()/fullInt_val
        signalInt_val=signalInt.getVal()/fullInt_val

        print "Events Number in MC Dataset:"
        self.workspace4fit_.var("rrv_number_dataset_sb_lo"+label+"_"+self.channel+"_mj").Print();
        self.workspace4fit_.var("rrv_number_dataset_signal_region"+label+"_"+self.channel+"_mj").Print();
        self.workspace4fit_.var("rrv_number_dataset_sb_hi"+label+"_"+self.channel+"_mj").Print();

        print "Events Number get from fit:"
        rrv_tmp=self.workspace4fit_.var("rrv_number"+label+"_"+self.channel+"_mj");
        rrv_tmp.Print();
        print "Events Number in sideband_low :%s"%(rrv_tmp.getVal()*sb_loInt_val)
        print "Events Number in Signal Region:%s"%(rrv_tmp.getVal()*signalInt_val)
        print "Events Number in sideband_high:%s"%(rrv_tmp.getVal()*sb_hiInt_val)
        print "Total Number in sidebands     :%s"%(rrv_tmp.getVal()*(sb_loInt_val+sb_hiInt_val)  )
        print "Ratio signal_region/sidebands        :%s"%(signalInt_val/(sb_loInt_val+sb_hiInt_val)  )

        #save to file
        self.file_out.write( "\n%s++++++++++++++++++++++++++++++++++++"%(label) )
        self.file_out.write( "\nEvents Number in sideband_low  from dataset:%s"%(self.workspace4fit_.var("rrv_number_dataset_sb_lo"+label+"_"+self.channel+"_mj").getVal() ) )
        self.file_out.write( "\nEvents Number in Signal Region from dataset:%s"%(self.workspace4fit_.var("rrv_number_dataset_signal_region"+label+"_"+self.channel+"_mj").getVal() ) )
        self.file_out.write( "\nEvents Number in sideband_high from dataset:%s"%(self.workspace4fit_.var("rrv_number_dataset_sb_hi"+label+"_"+self.channel+"_mj").getVal() ) )
        self.file_out.write( "\nTotal  Number in sidebands     from dataset:%s"%(self.workspace4fit_.var("rrv_number_dataset_sb_lo"+label+"_"+self.channel+"_mj").getVal()+ self.workspace4fit_.var("rrv_number_dataset_sb_hi"+label+"_"+self.channel+"_mj").getVal() ) )
        self.file_out.write( "\nRatio signal_region/sidebands  from dataset:%s"%(self.workspace4fit_.var("rrv_number_dataset_signal_region"+label+"_"+self.channel+"_mj").getVal()/(self.workspace4fit_.var("rrv_number_dataset_sb_lo"+label+"_"+self.channel+"_mj").getVal()+ self.workspace4fit_.var("rrv_number_dataset_sb_hi"+label+"_"+self.channel+"_mj").getVal()) ) )

        self.file_out.write( "\nEvents Number in sideband_low  from fitting:%s"%(rrv_tmp.getVal()*sb_loInt_val) )
        self.file_out.write( "\nEvents Number in Signal Region from fitting:%s"%(rrv_tmp.getVal()*signalInt_val) )
        self.file_out.write( "\nEvents Number in sideband_high from fitting:%s"%(rrv_tmp.getVal()*sb_hiInt_val) )
        self.file_out.write( "\nTotal  Number in sidebands     from fitting:%s"%(rrv_tmp.getVal()*(sb_loInt_val+sb_hiInt_val)  ) )
        self.file_out.write( "\nRatio signal_region/sidebands  from fitting:%s"%(signalInt_val/(sb_loInt_val+sb_hiInt_val)  ) )


    ######## ++++++++++++++
    def get_mlvj_normalization_insignalregion(self, label, model_name=""):
        print "get mlvj normalization"
        print model_name
        if model_name=="": model = self.workspace4fit_.pdf("model"+label+"_signal_region"+"_"+self.channel+"_mlvj");
        else: model = self.workspace4fit_.pdf(model_name);

        rrv_mass_lvj = self.workspace4fit_.var("rrv_mass_lvj");

        fullInt   = model.createIntegral(RooArgSet(rrv_mass_lvj),RooArgSet(rrv_mass_lvj) );
        signalInt = model.createIntegral(RooArgSet(rrv_mass_lvj),RooArgSet(rrv_mass_lvj),("signal_region"));
        
        fullInt_val=fullInt.getVal()
        signalInt_val=signalInt.getVal()/fullInt_val

        print label+"signalInt=%s"%(signalInt_val)

        print "Events Number in MC Dataset:"
        self.workspace4fit_.var("rrv_number_dataset_signal_region"+label+"_"+self.channel+"_mlvj").Print();
        self.workspace4fit_.var("rrv_number_dataset_AllRange"+label+"_"+self.channel+"_mlvj").Print();

        print "Events Number get from fit:"
        rrv_tmp=self.workspace4fit_.var("rrv_number"+label+"_signal_region"+"_"+self.channel+"_mlvj");
        rrv_tmp.Print();#raw_input("ENTER");
        print "\nEvents Number in Signal Region from fitting: %s"%(rrv_tmp.getVal()*signalInt_val)

        #save to file
        self.file_out.write( "\n%s++++++++++++++++++++++++++++++++++++"%(label) )
        self.file_out.write( "\nEvents Number in All Region from dataset   : %s"%(self.workspace4fit_.var("rrv_number_dataset_AllRange"+label+"_"+self.channel+"_mlvj").getVal()) )
        self.file_out.write( "\nEvents Number in Signal Region from dataset: %s"%(self.workspace4fit_.var("rrv_number_dataset_signal_region"+label+"_"+self.channel+"_mlvj").getVal()) )
        self.file_out.write( "\nRatio signal_region/all_range from dataset  :%s"%(self.workspace4fit_.var("rrv_number_dataset_signal_region"+label+"_"+self.channel+"_mlvj").getVal()/self.workspace4fit_.var("rrv_number_dataset_AllRange"+label+"_"+self.channel+"_mlvj").getVal() ) )
        self.file_out.write( "\nEvents Number in All Region from fitting   : %s\n"%(rrv_tmp.getVal()) )
        self.file_out.write( "\nEvents Number in Signal Region from fitting: %s\n"%(rrv_tmp.getVal()*signalInt_val) )
        self.file_out.write( "\nRatio signal_region/all_range from fitting :%s"%(signalInt_val ) )

        if not self.workspace4fit_.var("rrv_number_fitting_signal_region"+label+"_"+self.channel+"_mlvj"):
            rrv_number_fitting_signal_region_mlvj=RooRealVar("rrv_number_fitting_signal_region"+label+"_"+self.channel+"_mlvj","rrv_number_fitting_signal_region"+label+"_"+self.channel+"_mlvj", rrv_tmp.getVal()*signalInt_val );
            getattr(self.workspace4fit_,"import")(rrv_number_fitting_signal_region_mlvj);
        else :
            self.workspace4fit_.var("rrv_number_fitting_signal_region"+label+"_"+self.channel+"_mlvj").setVal(rrv_tmp.getVal()*signalInt_val);
        self.workspace4fit_.var("rrv_number_fitting_signal_region"+label+"_"+self.channel+"_mlvj").Print();#raw_input("ENTER"); 
        #if label=="_WJets0" and self.number_WJets_insideband!=-1: #prepare Limit of WJet Norm
        #    self.datadriven_alpha_WJets_counting = rrv_tmp.getVal()*signalInt_val/self.number_WJets_insideband 

    ######## ++++++++++++++
    def print_limit_datacard(self, mode ,params_list=[] ): #mode:unbin or counting
        print "print_limit_datacard for %s"%(mode)
        if not (mode == "unbin" or mode == "counting"):
            print "print_limit_datacard use wrong mode: %s"%(mode);raw_input("ENTER");
        datacard_out=open(getattr(self,"file_datacard_%s"%(mode)),"w");

        datacard_out.write( "imax 1" )
        datacard_out.write( "\njmax 4" )
        datacard_out.write( "\nkmax *" )
        datacard_out.write( "\n--------------- ")
        if mode == "unbin":
            fnOnly = ntpath.basename(self.file_rlt_root)
            datacard_out.write( "\nshapes * * %s %s:$PROCESS_%s"%(fnOnly, self.workspace4limit_.GetName(), self.channel))
            datacard_out.write( "\n--------------- ")
        datacard_out.write( "\nbin 1 ")
        if mode == "unbin":
            datacard_out.write( "\nobservation %0.2f "%(self.workspace4limit_.data("data_obs_%s"%(self.channel)).sumEntries()) )
        if mode == "counting":
            datacard_out.write( "\nobservation %0.2f "%(self.workspace4limit_.var("observation_for_counting").getVal()) )
        datacard_out.write( "\n------------------------------" )
        datacard_out.write( "\nbin                1                       1        1        1       1" )
        datacard_out.write( "\nprocess            %s             WJets    TTbar    STop    VV "%(self.signal_sample) )
        datacard_out.write( "\nprocess            -1                      1        2        3       4" )
        if mode == "unbin":
            datacard_out.write( "\nrate               %0.5f                %0.3f   %0.3f    %0.3f    %0.3f "%(self.workspace4limit_.var("rate_%s_for_unbin"%(self.signal_sample)).getVal(),                                                                                self.workspace4limit_.var("rate_WJets_for_unbin").getVal(), self.workspace4limit_.var("rate_TTbar_for_unbin").getVal(), self.workspace4limit_.var("rate_STop_for_unbin").getVal(), self.workspace4limit_.var("rate_VV_for_unbin").getVal()  ) )
        if mode == "counting":
            datacard_out.write( "\nrate               %0.5f             %0.3f   %0.3f    %0.3f    %0.3f"%(self.workspace4limit_.var("rate_%s_for_counting"%(self.signal_sample)).getVal(),                                                                                   self.workspace4limit_.var("rate_WJets_for_counting").getVal(), self.workspace4limit_.var("rate_TTbar_for_counting").getVal(), self.workspace4limit_.var("rate_STop_for_counting").getVal(), self.workspace4limit_.var("rate_VV_for_counting").getVal()  ) )
        datacard_out.write( "\n-------------------------------- " )
        datacard_out.write( "\nlumi     lnN       %0.3f                   -        %0.3f   %0.3f   %0.3f"%(1.+self.lumi_uncertainty,                         1.+self.lumi_uncertainty,1.+self.lumi_uncertainty,1.+self.lumi_uncertainty) )
        datacard_out.write( "\nXS_STop  lnN       -                       -        -       %0.3f   -"%(1+self.XS_STop_uncertainty) )
        datacard_out.write( "\nXS_VV    lnN       -                       -        -       -       %0.3f"%(1+self.XS_VV_uncertainty) )
        #print self.number_WJets_insideband; raw_input("ENTER");
        if self.number_WJets_insideband >0:
            datacard_out.write( "\nWJ_norm gmN %0.3f        %0.3f           -      -        -"%(self.number_WJets_insideband, getattr(self, "datadriven_alpha_WJets_%s"%(mode)) ) )
        else:
            datacard_out.write( "\nWJ_norm_%s_%s lnN     -                       %0.3f    -       -       -"%(self.channel, self.wtagger_label, 1+ self.workspace4limit_.var("rate_WJets_for_unbin").getError()/self.workspace4limit_.var("rate_WJets_for_unbin").getVal() ) );
        datacard_out.write( "\nTop_norm_%s_%s lnN    -                       -        %0.3f   %0.3f   -"%(self.channel,self.wtagger_label, 1+self.rrv_wtagger_eff_reweight_forT.getError()/self.rrv_wtagger_eff_reweight_forT.getVal(), 1+self.rrv_wtagger_eff_reweight_forT.getError()/self.rrv_wtagger_eff_reweight_forT.getVal() ) );
        datacard_out.write( "\nwtagger_%s_%s lnN     %0.3f                   -        -       -       %0.3f"%(self.channel,self.wtagger_label, 1+self.rrv_wtagger_eff_reweight_forV.getError()/self.rrv_wtagger_eff_reweight_forV.getVal(),                                                                                              1+self.rrv_wtagger_eff_reweight_forV.getError()/self.rrv_wtagger_eff_reweight_forV.getVal() ) );
        datacard_out.write( "\n#btagger_%s lnN     %0.3f                   -        %0.3f   %0.3f   %0.3f"%(self.channel, 1+self.btag_scale_uncertainty,                                1+self.btag_scale_uncertainty, 1+self.btag_scale_uncertainty, 1+self.btag_scale_uncertainty ) );
        datacard_out.write( "\nJetMass_%s_%s lnN     -                       %0.3f    %0.3f   %0.3f   %0.3f"%(self.channel,self.wtagger_label, 1+self.WJets_normlization_uncertainty_from_jet_mass, 1+self.TTbar_normlization_uncertainty_from_jet_mass, 1+self.STop_normlization_uncertainty_from_jet_mass, 1+self.VV_normlization_uncertainty_from_jet_mass ) )
        datacard_out.write( "\ntrigger_%s lnN     %0.3f                   -        %0.3f   %0.3f   %0.3f"%(self.channel,                               1+self.lep_trigger_uncertainty,1+self.lep_trigger_uncertainty,1+self.lep_trigger_uncertainty,1+self.lep_trigger_uncertainty ) );
        datacard_out.write( "\neff_%s   lnN       %0.3f                   -        %0.3f   %0.3f   %0.3f"%(self.channel,                               1+self.lep_eff_uncertainty,                           1+self.lep_eff_uncertainty,1+self.lep_eff_uncertainty,1+self.lep_eff_uncertainty ) );
        datacard_out.write( "\nlepton_scale_%s   lnN       %0.3f                   -        -   -   -"%(self.channel,                               1+self.signal_lepton_energy_scale_uncertainty));
        datacard_out.write( "\nlepton_res_%s     lnN       %0.3f                   -        -   -   -"%(self.channel,                                1+self.signal_lepton_energy_res_uncertainty));
        datacard_out.write( "\njet_scale_%s       lnN       %0.3f                   -        -   -   -"%(self.channel,                                1+self.signal_jet_energy_scale_uncertainty));
        datacard_out.write( "\njet_res_%s        lnN       %0.3f                   -        -   -   -"%(self.channel,                                1+self.signal_jet_energy_res_uncertainty));
        datacard_out.write( "\nbtag_eff_%s       lnN       %0.3f                   -        -   -   -"%(self.channel,                                1+self.signal_btag_uncertainty));

        if mode == "unbin":
            for i in range(len(params_list)):
                print " param list  ",params_list[i].GetName() ;
                if TString(params_list[i].GetName()).Contains("Deco_TTbar_signal_region"):
                    datacard_out.write( "\n%s param  %0.3f  %0.3f "%( params_list[i].GetName(), params_list[i].getVal(), params_list[i].getError() ) ) 
                else:
                    datacard_out.write( "\n%s param  %0.3f  %0.3f "%( params_list[i].GetName(), params_list[i].getVal(), params_list[i].getError() ) ) 
        if mode == "counting":
            datacard_out.write( "\nShape_%s_%s    lnN       -         -             %0.3f    -       -       -"%(self.channel,self.wtagger_label, 1+self.rrv_counting_uncertainty_from_shape_uncertainty.getError()))

    ######## ++++++++++++++
    def prepare_limit(self,mode):
        print "prepare_limit for %s method"%(mode);
        #prepare for Limit
        getattr(self.workspace4limit_,"import")(self.workspace4fit_.var("rrv_mass_lvj"));
        
        getattr(self.workspace4limit_,"import")(self.workspace4fit_.var("rrv_number_fitting_signal_region_%s_%s_mlvj"%(self.signal_sample,self.channel)).clone("rate_%s_for_counting"%(self.signal_sample)) )
        getattr(self.workspace4limit_,"import")(self.workspace4fit_.var("rrv_number_fitting_signal_region_WJets0_%s_mlvj"%(self.channel)).clone("rate_WJets_for_counting"))
        getattr(self.workspace4limit_,"import")(self.workspace4fit_.var("rrv_number_fitting_signal_region_VV_%s_mlvj"%(self.channel)).clone("rate_VV_for_counting"))
        getattr(self.workspace4limit_,"import")(self.workspace4fit_.var("rrv_number_fitting_signal_region_TTbar_%s_mlvj"%(self.channel)).clone("rate_TTbar_for_counting"))
        getattr(self.workspace4limit_,"import")(self.workspace4fit_.var("rrv_number_fitting_signal_region_STop_%s_mlvj"%(self.channel)).clone("rate_STop_for_counting"))

        getattr(self.workspace4limit_,"import")(self.workspace4fit_.var("rrv_number_%s_signal_region_%s_mlvj"%(self.signal_sample, 
self.channel)).clone("rate_%s_for_unbin"%(self.signal_sample)));
        getattr(self.workspace4limit_,"import")(self.workspace4fit_.var("rrv_number_WJets0_signal_region_%s_mlvj"%(self.channel)).clone("rate_WJets_for_unbin"));
        getattr(self.workspace4limit_,"import")(self.workspace4fit_.var("rrv_number_VV_signal_region_%s_mlvj"%(self.channel)).clone("rate_VV_for_unbin"));
        getattr(self.workspace4limit_,"import")(self.workspace4fit_.var("rrv_number_TTbar_signal_region_%s_mlvj"%(self.channel)).clone("rate_TTbar_for_unbin"));
        getattr(self.workspace4limit_,"import")(self.workspace4fit_.var("rrv_number_STop_signal_region_%s_mlvj"%(self.channel)).clone("rate_STop_for_unbin"));
        self.workspace4limit_.var("rate_VV_for_unbin").setError(self.workspace4limit_.var("rate_VV_for_unbin").getVal()*TMath.Sqrt( self.lumi_uncertainty*self.lumi_uncertainty + self.rrv_wtagger_eff_reweight_forV.getError()/self.rrv_wtagger_eff_reweight_forV.getVal()*self.rrv_wtagger_eff_reweight_forV.getError()/self.rrv_wtagger_eff_reweight_forV.getVal() +self.XS_VV_uncertainty*self.XS_VV_uncertainty ) );
        self.workspace4limit_.var("rate_STop_for_unbin").setError(self.workspace4limit_.var("rate_STop_for_unbin").getVal()*TMath.Sqrt( self.lumi_uncertainty*self.lumi_uncertainty + self.rrv_wtagger_eff_reweight_forT.getError()/self.rrv_wtagger_eff_reweight_forT.getVal()*self.rrv_wtagger_eff_reweight_forT.getError()/self.rrv_wtagger_eff_reweight_forT.getVal() +self.XS_STop_uncertainty*self.XS_STop_uncertainty ) );
        self.workspace4limit_.var("rate_TTbar_for_unbin").setError(self.workspace4limit_.var("rate_TTbar_for_unbin").getVal()*TMath.Sqrt( self.lumi_uncertainty*self.lumi_uncertainty + self.rrv_wtagger_eff_reweight_forT.getError()/self.rrv_wtagger_eff_reweight_forT.getVal()*self.rrv_wtagger_eff_reweight_forT.getError()/self.rrv_wtagger_eff_reweight_forT.getVal() )) #+self.XS_TTbar_uncertainty*self.XS_TTbar_uncertainty ) );
 
        getattr(self.workspace4limit_,"import")(self.workspace4fit_.data("rdataset_data_signal_region_%s_mlvj"%(self.channel)).Clone("data_obs_%s"%(self.channel)))
        if mode=="sideband_correction_method1":
            getattr(self.workspace4limit_,"import")(self.workspace4fit_.pdf("model_pdf_WJets0_signal_region_%s_after_correct_mlvj"%(self.channel)).clone("WJets_%s"%(self.channel)))
            self.workspace4limit_.allVars().Print();
        getattr(self.workspace4limit_,"import")(self.workspace4fit_.pdf("model_pdf_TTbar_signal_region_%s_mlvj_Deco_TTbar_signal_region_%s_%s_mlvj"%(self.channel, self.channel, self.wtagger_label)).clone("TTbar_%s"%(self.channel)))
        getattr(self.workspace4limit_,"import")(self.workspace4fit_.pdf("model_pdf_STop_signal_region_%s_mlvj"%(self.channel)).clone("STop_%s"%(self.channel)))
        getattr(self.workspace4limit_,"import")(self.workspace4fit_.pdf("model_pdf_VV_signal_region_%s_mlvj"%(self.channel)).clone("VV_%s"%(self.channel)))
        
        getattr(self.workspace4limit_,"import")(self.workspace4fit_.pdf("model_pdf_%s_signal_region_%s_mlvj"%(self.signal_sample,self.channel)).clone(self.signal_sample+"_%s"%(self.channel)))

        rrv_x=self.workspace4limit_.var("rrv_mass_lvj");
        self.fix_Pdf(self.workspace4limit_.pdf("TTbar_%s"%(self.channel)), RooArgSet(rrv_x) );
        self.fix_Pdf(self.workspace4limit_.pdf("STop_%s"%(self.channel)), RooArgSet(rrv_x));
        self.fix_Pdf(self.workspace4limit_.pdf("VV_%s"%(self.channel)), RooArgSet(rrv_x));
        self.fix_Pdf(self.workspace4limit_.pdf("WJets_%s"%(self.channel)), RooArgSet(rrv_x));

        params_list=[];
        shape_para_error_WJets0=1.4;# for sb_lo fitting
        shape_para_error_alpha=1.4;#for alpha
        if self.MODEL_4_mlvj=="ErfPowExp_v1" or self.MODEL_4_mlvj=="ErfPow2_v1" or self.MODEL_4_mlvj=="ErfExp_v1":
              shape_para_error_alpha=1.4;
        else: shape_para_error_alpha=2.;
                          
        shape_para_error_TTbar=2.;
  
        if mode=="sideband_correction_method1":
            if self.MODEL_4_mlvj=="ErfExp_v1" or self.MODEL_4_mlvj=="ErfPow_v1" or self.MODEL_4_mlvj=="2Exp" :
                self.workspace4limit_.var("Deco_WJets0_sb_lo_from_fitting_%s_%s_mlvj_eig0"%(self.channel, self.wtagger_label)).setError(shape_para_error_WJets0);
                self.workspace4limit_.var("Deco_WJets0_sb_lo_from_fitting_%s_%s_mlvj_eig1"%(self.channel, self.wtagger_label)).setError(shape_para_error_WJets0);
                self.workspace4limit_.var("Deco_WJets0_sb_lo_from_fitting_%s_%s_mlvj_eig2"%(self.channel, self.wtagger_label)).setError(shape_para_error_WJets0);
                self.workspace4limit_.var("Deco_WJets0_sb_lo_from_fitting_%s_%s_mlvj_eig3"%(self.channel, self.wtagger_label)).setError(shape_para_error_WJets0);
                params_list.append(self.workspace4limit_.var("Deco_WJets0_sb_lo_from_fitting_%s_%s_mlvj_eig0"%(self.channel, self.wtagger_label)));
                params_list.append(self.workspace4limit_.var("Deco_WJets0_sb_lo_from_fitting_%s_%s_mlvj_eig1"%(self.channel, self.wtagger_label)));
                params_list.append(self.workspace4limit_.var("Deco_WJets0_sb_lo_from_fitting_%s_%s_mlvj_eig2"%(self.channel, self.wtagger_label)));
                params_list.append(self.workspace4limit_.var("Deco_WJets0_sb_lo_from_fitting_%s_%s_mlvj_eig3"%(self.channel, self.wtagger_label)));
                self.FloatingParams.add(self.workspace4limit_.var("Deco_WJets0_sb_lo_from_fitting_%s_%s_mlvj_eig0"%(self.channel, self.wtagger_label)) );
                self.FloatingParams.add(self.workspace4limit_.var("Deco_WJets0_sb_lo_from_fitting_%s_%s_mlvj_eig1"%(self.channel, self.wtagger_label)) );
                self.FloatingParams.add(self.workspace4limit_.var("Deco_WJets0_sb_lo_from_fitting_%s_%s_mlvj_eig2"%(self.channel, self.wtagger_label)) );
                self.FloatingParams.add(self.workspace4limit_.var("Deco_WJets0_sb_lo_from_fitting_%s_%s_mlvj_eig3"%(self.channel, self.wtagger_label)) );

                self.workspace4limit_.var("Deco_WJets0_sb_lo_sim_%s_%s_mlvj_eig0"%(self.channel, self.wtagger_label)).setError(shape_para_error_alpha); 
                params_list.append(self.workspace4limit_.var("Deco_WJets0_sb_lo_sim_%s_%s_mlvj_eig0"%(self.channel, self.wtagger_label)))
                self.workspace4limit_.var("Deco_WJets0_sb_lo_sim_%s_%s_mlvj_eig1"%(self.channel, self.wtagger_label)).setError(shape_para_error_alpha); 
                params_list.append(self.workspace4limit_.var("Deco_WJets0_sb_lo_sim_%s_%s_mlvj_eig1"%(self.channel, self.wtagger_label)))
                self.workspace4limit_.var("Deco_WJets0_sb_lo_sim_%s_%s_mlvj_eig2"%(self.channel, self.wtagger_label)).setError(shape_para_error_alpha); 
                params_list.append(self.workspace4limit_.var("Deco_WJets0_sb_lo_sim_%s_%s_mlvj_eig2"%(self.channel, self.wtagger_label)))
                self.workspace4limit_.var("Deco_WJets0_sb_lo_sim_%s_%s_mlvj_eig3"%(self.channel, self.wtagger_label)).setError(shape_para_error_alpha); 
                params_list.append(self.workspace4limit_.var("Deco_WJets0_sb_lo_sim_%s_%s_mlvj_eig3"%(self.channel, self.wtagger_label)))
                self.workspace4limit_.var("Deco_WJets0_sb_lo_sim_%s_%s_mlvj_eig4"%(self.channel, self.wtagger_label)).setError(shape_para_error_alpha); 
                params_list.append(self.workspace4limit_.var("Deco_WJets0_sb_lo_sim_%s_%s_mlvj_eig4"%(self.channel, self.wtagger_label)))
                self.workspace4limit_.var("Deco_WJets0_sb_lo_sim_%s_%s_mlvj_eig5"%(self.channel, self.wtagger_label)).setError(shape_para_error_alpha); 
                params_list.append(self.workspace4limit_.var("Deco_WJets0_sb_lo_sim_%s_%s_mlvj_eig5"%(self.channel, self.wtagger_label)))
                self.FloatingParams.add(self.workspace4limit_.var("Deco_WJets0_sb_lo_sim_%s_%s_mlvj_eig0"%(self.channel, self.wtagger_label)) );
                self.FloatingParams.add(self.workspace4limit_.var("Deco_WJets0_sb_lo_sim_%s_%s_mlvj_eig1"%(self.channel, self.wtagger_label)) );
                self.FloatingParams.add(self.workspace4limit_.var("Deco_WJets0_sb_lo_sim_%s_%s_mlvj_eig2"%(self.channel, self.wtagger_label)) );
                self.FloatingParams.add(self.workspace4limit_.var("Deco_WJets0_sb_lo_sim_%s_%s_mlvj_eig3"%(self.channel, self.wtagger_label)) );
                self.FloatingParams.add(self.workspace4limit_.var("Deco_WJets0_sb_lo_sim_%s_%s_mlvj_eig4"%(self.channel, self.wtagger_label)) );
                self.FloatingParams.add(self.workspace4limit_.var("Deco_WJets0_sb_lo_sim_%s_%s_mlvj_eig5"%(self.channel, self.wtagger_label)) );

                self.workspace4limit_.var("Deco_TTbar_signal_region_%s_%s_mlvj_eig0"%(self.channel, self.wtagger_label)).setError(shape_para_error_TTbar);
                self.workspace4limit_.var("Deco_TTbar_signal_region_%s_%s_mlvj_eig1"%(self.channel, self.wtagger_label)).setError(shape_para_error_TTbar);
                self.workspace4limit_.var("Deco_TTbar_signal_region_%s_%s_mlvj_eig2"%(self.channel, self.wtagger_label)).setError(shape_para_error_TTbar);
                params_list.append(self.workspace4limit_.var("Deco_TTbar_signal_region_%s_%s_mlvj_eig0"%(self.channel, self.wtagger_label)));
                params_list.append(self.workspace4limit_.var("Deco_TTbar_signal_region_%s_%s_mlvj_eig1"%(self.channel, self.wtagger_label)));
                params_list.append(self.workspace4limit_.var("Deco_TTbar_signal_region_%s_%s_mlvj_eig2"%(self.channel, self.wtagger_label)));

            if self.MODEL_4_mlvj=="ErfPow2_v1" or self.MODEL_4_mlvj=="ErfPowExp_v1" :
                self.workspace4limit_.var("Deco_WJets0_sb_lo_from_fitting_%s_%s_mlvj_eig0"%(self.channel, self.wtagger_label)).setError(shape_para_error_WJets0);
                self.workspace4limit_.var("Deco_WJets0_sb_lo_from_fitting_%s_%s_mlvj_eig1"%(self.channel, self.wtagger_label)).setError(shape_para_error_WJets0);
                self.workspace4limit_.var("Deco_WJets0_sb_lo_from_fitting_%s_%s_mlvj_eig2"%(self.channel, self.wtagger_label)).setError(shape_para_error_WJets0);
                self.workspace4limit_.var("Deco_WJets0_sb_lo_from_fitting_%s_%s_mlvj_eig3"%(self.channel, self.wtagger_label)).setError(shape_para_error_WJets0);
                self.workspace4limit_.var("Deco_WJets0_sb_lo_from_fitting_%s_%s_mlvj_eig4"%(self.channel, self.wtagger_label)).setError(shape_para_error_WJets0);
                params_list.append(self.workspace4limit_.var("Deco_WJets0_sb_lo_from_fitting_%s_%s_mlvj_eig0"%(self.channel, self.wtagger_label)));
                params_list.append(self.workspace4limit_.var("Deco_WJets0_sb_lo_from_fitting_%s_%s_mlvj_eig1"%(self.channel, self.wtagger_label)));
                params_list.append(self.workspace4limit_.var("Deco_WJets0_sb_lo_from_fitting_%s_%s_mlvj_eig2"%(self.channel, self.wtagger_label)));
                params_list.append(self.workspace4limit_.var("Deco_WJets0_sb_lo_from_fitting_%s_%s_mlvj_eig3"%(self.channel, self.wtagger_label)));
                params_list.append(self.workspace4limit_.var("Deco_WJets0_sb_lo_from_fitting_%s_%s_mlvj_eig4"%(self.channel, self.wtagger_label)));
                self.FloatingParams.add(self.workspace4limit_.var("Deco_WJets0_sb_lo_from_fitting_%s_%s_mlvj_eig0"%(self.channel, self.wtagger_label)) );
                self.FloatingParams.add(self.workspace4limit_.var("Deco_WJets0_sb_lo_from_fitting_%s_%s_mlvj_eig1"%(self.channel, self.wtagger_label)) );
                self.FloatingParams.add(self.workspace4limit_.var("Deco_WJets0_sb_lo_from_fitting_%s_%s_mlvj_eig2"%(self.channel, self.wtagger_label)) );
                self.FloatingParams.add(self.workspace4limit_.var("Deco_WJets0_sb_lo_from_fitting_%s_%s_mlvj_eig3"%(self.channel, self.wtagger_label)) );
                self.FloatingParams.add(self.workspace4limit_.var("Deco_WJets0_sb_lo_from_fitting_%s_%s_mlvj_eig4"%(self.channel, self.wtagger_label)) );
                self.workspace4limit_.var("Deco_WJets0_sb_lo_sim_%s_%s_mlvj_eig0"%(self.channel, self.wtagger_label)).setError(shape_para_error_alpha); 
                params_list.append(self.workspace4limit_.var("Deco_WJets0_sb_lo_sim_%s_%s_mlvj_eig0"%(self.channel, self.wtagger_label)))
                self.workspace4limit_.var("Deco_WJets0_sb_lo_sim_%s_%s_mlvj_eig1"%(self.channel, self.wtagger_label)).setError(shape_para_error_alpha); 
                params_list.append(self.workspace4limit_.var("Deco_WJets0_sb_lo_sim_%s_%s_mlvj_eig1"%(self.channel, self.wtagger_label)))
                self.workspace4limit_.var("Deco_WJets0_sb_lo_sim_%s_%s_mlvj_eig2"%(self.channel, self.wtagger_label)).setError(shape_para_error_alpha); 
                params_list.append(self.workspace4limit_.var("Deco_WJets0_sb_lo_sim_%s_%s_mlvj_eig2"%(self.channel, self.wtagger_label)))
                self.workspace4limit_.var("Deco_WJets0_sb_lo_sim_%s_%s_mlvj_eig3"%(self.channel, self.wtagger_label)).setError(shape_para_error_alpha); 
                params_list.append(self.workspace4limit_.var("Deco_WJets0_sb_lo_sim_%s_%s_mlvj_eig3"%(self.channel, self.wtagger_label)))
                self.workspace4limit_.var("Deco_WJets0_sb_lo_sim_%s_%s_mlvj_eig4"%(self.channel, self.wtagger_label)).setError(shape_para_error_alpha); 
                params_list.append(self.workspace4limit_.var("Deco_WJets0_sb_lo_sim_%s_%s_mlvj_eig4"%(self.channel, self.wtagger_label)))
                self.workspace4limit_.var("Deco_WJets0_sb_lo_sim_%s_%s_mlvj_eig5"%(self.channel, self.wtagger_label)).setError(shape_para_error_alpha); 
                params_list.append(self.workspace4limit_.var("Deco_WJets0_sb_lo_sim_%s_%s_mlvj_eig5"%(self.channel, self.wtagger_label)))
                self.workspace4limit_.var("Deco_WJets0_sb_lo_sim_%s_%s_mlvj_eig6"%(self.channel, self.wtagger_label)).setError(shape_para_error_alpha); 
                params_list.append(self.workspace4limit_.var("Deco_WJets0_sb_lo_sim_%s_%s_mlvj_eig6"%(self.channel, self.wtagger_label)))
                self.workspace4limit_.var("Deco_WJets0_sb_lo_sim_%s_%s_mlvj_eig7"%(self.channel, self.wtagger_label)).setError(shape_para_error_alpha); 
                params_list.append(self.workspace4limit_.var("Deco_WJets0_sb_lo_sim_%s_%s_mlvj_eig7"%(self.channel, self.wtagger_label)))
                self.FloatingParams.add(self.workspace4limit_.var("Deco_WJets0_sb_lo_sim_%s_%s_mlvj_eig0"%(self.channel, self.wtagger_label)) );
                self.FloatingParams.add(self.workspace4limit_.var("Deco_WJets0_sb_lo_sim_%s_%s_mlvj_eig1"%(self.channel, self.wtagger_label)) );
                self.FloatingParams.add(self.workspace4limit_.var("Deco_WJets0_sb_lo_sim_%s_%s_mlvj_eig2"%(self.channel, self.wtagger_label)) );
                self.FloatingParams.add(self.workspace4limit_.var("Deco_WJets0_sb_lo_sim_%s_%s_mlvj_eig3"%(self.channel, self.wtagger_label)) );
                self.FloatingParams.add(self.workspace4limit_.var("Deco_WJets0_sb_lo_sim_%s_%s_mlvj_eig4"%(self.channel, self.wtagger_label)) );
                self.FloatingParams.add(self.workspace4limit_.var("Deco_WJets0_sb_lo_sim_%s_%s_mlvj_eig5"%(self.channel, self.wtagger_label)) );
                self.FloatingParams.add(self.workspace4limit_.var("Deco_WJets0_sb_lo_sim_%s_%s_mlvj_eig6"%(self.channel, self.wtagger_label)) );
                self.FloatingParams.add(self.workspace4limit_.var("Deco_WJets0_sb_lo_sim_%s_%s_mlvj_eig7"%(self.channel, self.wtagger_label)) );

                self.workspace4limit_.var("Deco_TTbar_signal_region_%s_%s_mlvj_eig0"%(self.channel, self.wtagger_label)).setError(shape_para_error_TTbar);
                self.workspace4limit_.var("Deco_TTbar_signal_region_%s_%s_mlvj_eig1"%(self.channel, self.wtagger_label)).setError(shape_para_error_TTbar);
                self.workspace4limit_.var("Deco_TTbar_signal_region_%s_%s_mlvj_eig2"%(self.channel, self.wtagger_label)).setError(shape_para_error_TTbar);
                self.workspace4limit_.var("Deco_TTbar_signal_region_%s_%s_mlvj_eig3"%(self.channel, self.wtagger_label)).setError(shape_para_error_TTbar);
                params_list.append(self.workspace4limit_.var("Deco_TTbar_signal_region_%s_%s_mlvj_eig0"%(self.channel, self.wtagger_label)));
                params_list.append(self.workspace4limit_.var("Deco_TTbar_signal_region_%s_%s_mlvj_eig1"%(self.channel, self.wtagger_label)));
                params_list.append(self.workspace4limit_.var("Deco_TTbar_signal_region_%s_%s_mlvj_eig2"%(self.channel, self.wtagger_label)));
                params_list.append(self.workspace4limit_.var("Deco_TTbar_signal_region_%s_%s_mlvj_eig3"%(self.channel, self.wtagger_label)));
                #if options.closuretest==0:
                # self.FloatingParams.add(self.workspace4limit_.var("Deco_TTbar_signal_region_%s_mlvj_eig0"%(self.channel)));
                # self.FloatingParams.add(self.workspace4limit_.var("Deco_TTbar_signal_region_%s_mlvj_eig1"%(self.channel)));
                # self.FloatingParams.add(self.workspace4limit_.var("Deco_TTbar_signal_region_%s_mlvj_eig2"%(self.channel)));
                # self.FloatingParams.add(self.workspace4limit_.var("Deco_TTbar_signal_region_%s_mlvj_eig3"%(self.channel)));

            if self.MODEL_4_mlvj=="Exp" or self.MODEL_4_mlvj=="Pow" :
                self.workspace4limit_.var("Deco_WJets0_sb_lo_from_fitting_%s_%s_mlvj_eig0"%(self.channel, self.wtagger_label)).setError(shape_para_error_WJets0);
                self.workspace4limit_.var("Deco_WJets0_sb_lo_from_fitting_%s_%s_mlvj_eig1"%(self.channel, self.wtagger_label)).setError(shape_para_error_WJets0);
                params_list.append(self.workspace4limit_.var("Deco_WJets0_sb_lo_from_fitting_%s_%s_mlvj_eig0"%(self.channel, self.wtagger_label)));
                params_list.append(self.workspace4limit_.var("Deco_WJets0_sb_lo_from_fitting_%s_%s_mlvj_eig1"%(self.channel, self.wtagger_label)));
                self.FloatingParams.add(self.workspace4limit_.var("Deco_WJets0_sb_lo_from_fitting_%s_%s_mlvj_eig0"%(self.channel, self.wtagger_label)) );
                self.FloatingParams.add(self.workspace4limit_.var("Deco_WJets0_sb_lo_from_fitting_%s_%s_mlvj_eig1"%(self.channel, self.wtagger_label)) );
                self.workspace4limit_.var("Deco_WJets0_sb_lo_sim_%s_%s_mlvj_eig0"%(self.channel, self.wtagger_label)).setError(shape_para_error_alpha); 
                params_list.append(self.workspace4limit_.var("Deco_WJets0_sb_lo_sim_%s_%s_mlvj_eig0"%(self.channel, self.wtagger_label)))
                self.workspace4limit_.var("Deco_WJets0_sb_lo_sim_%s_%s_mlvj_eig1"%(self.channel, self.wtagger_label)).setError(shape_para_error_alpha); 
                params_list.append(self.workspace4limit_.var("Deco_WJets0_sb_lo_sim_%s_%s_mlvj_eig1"%(self.channel, self.wtagger_label)))
                self.FloatingParams.add(self.workspace4limit_.var("Deco_WJets0_sb_lo_sim_%s_%s_mlvj_eig0"%(self.channel, self.wtagger_label)) );
                self.FloatingParams.add(self.workspace4limit_.var("Deco_WJets0_sb_lo_sim_%s_%s_mlvj_eig1"%(self.channel, self.wtagger_label)) );

                self.workspace4limit_.var("Deco_TTbar_signal_region_%s_%s_mlvj_eig0"%(self.channel, self.wtagger_label)).setError(shape_para_error_TTbar);
                params_list.append(self.workspace4limit_.var("Deco_TTbar_signal_region_%s_%s_mlvj_eig0"%(self.channel, self.wtagger_label)));
                #if options.closuretest==0:
                # self.FloatingParams.add(self.workspace4limit_.var("Deco_TTbar_signal_region_%s_mlvj_eig0"%(self.channel)));

            if self.MODEL_4_mlvj=="ExpN" or self.MODEL_4_mlvj=="ExpTail" or self.MODEL_4_mlvj=="Pow2" :
                self.workspace4limit_.var("Deco_WJets0_sb_lo_from_fitting_%s_%s_mlvj_eig0"%(self.channel, self.wtagger_label)).setError(shape_para_error_WJets0);
                self.workspace4limit_.var("Deco_WJets0_sb_lo_from_fitting_%s_%s_mlvj_eig1"%(self.channel, self.wtagger_label)).setError(shape_para_error_WJets0);
                self.workspace4limit_.var("Deco_WJets0_sb_lo_from_fitting_%s_%s_mlvj_eig2"%(self.channel, self.wtagger_label)).setError(shape_para_error_WJets0);
                params_list.append(self.workspace4limit_.var("Deco_WJets0_sb_lo_from_fitting_%s_%s_mlvj_eig0"%(self.channel, self.wtagger_label)));
                params_list.append(self.workspace4limit_.var("Deco_WJets0_sb_lo_from_fitting_%s_%s_mlvj_eig1"%(self.channel, self.wtagger_label)));
                params_list.append(self.workspace4limit_.var("Deco_WJets0_sb_lo_from_fitting_%s_%s_mlvj_eig2"%(self.channel, self.wtagger_label)));
                self.FloatingParams.add(self.workspace4limit_.var("Deco_WJets0_sb_lo_from_fitting_%s_%s_mlvj_eig0"%(self.channel, self.wtagger_label)) );
                self.FloatingParams.add(self.workspace4limit_.var("Deco_WJets0_sb_lo_from_fitting_%s_%s_mlvj_eig1"%(self.channel, self.wtagger_label)) );
                self.FloatingParams.add(self.workspace4limit_.var("Deco_WJets0_sb_lo_from_fitting_%s_%s_mlvj_eig2"%(self.channel, self.wtagger_label)) );
                self.workspace4limit_.var("Deco_WJets0_sb_lo_sim_%s_%s_mlvj_eig0"%(self.channel, self.wtagger_label)).setError(shape_para_error_alpha); 
                params_list.append(self.workspace4limit_.var("Deco_WJets0_sb_lo_sim_%s_%s_mlvj_eig0"%(self.channel, self.wtagger_label)))
                self.workspace4limit_.var("Deco_WJets0_sb_lo_sim_%s_%s_mlvj_eig1"%(self.channel, self.wtagger_label)).setError(shape_para_error_alpha); 
                params_list.append(self.workspace4limit_.var("Deco_WJets0_sb_lo_sim_%s_%s_mlvj_eig1"%(self.channel, self.wtagger_label)))
                self.workspace4limit_.var("Deco_WJets0_sb_lo_sim_%s_%s_mlvj_eig2"%(self.channel, self.wtagger_label)).setError(shape_para_error_alpha); 
                params_list.append(self.workspace4limit_.var("Deco_WJets0_sb_lo_sim_%s_%s_mlvj_eig2"%(self.channel, self.wtagger_label)))
                self.workspace4limit_.var("Deco_WJets0_sb_lo_sim_%s_%s_mlvj_eig3"%(self.channel, self.wtagger_label)).setError(shape_para_error_alpha); 
                params_list.append(self.workspace4limit_.var("Deco_WJets0_sb_lo_sim_%s_%s_mlvj_eig3"%(self.channel, self.wtagger_label)))
                self.FloatingParams.add(self.workspace4limit_.var("Deco_WJets0_sb_lo_sim_%s_%s_mlvj_eig0"%(self.channel, self.wtagger_label)) );
                self.FloatingParams.add(self.workspace4limit_.var("Deco_WJets0_sb_lo_sim_%s_%s_mlvj_eig1"%(self.channel, self.wtagger_label)) );
                self.FloatingParams.add(self.workspace4limit_.var("Deco_WJets0_sb_lo_sim_%s_%s_mlvj_eig2"%(self.channel, self.wtagger_label)) );
                self.FloatingParams.add(self.workspace4limit_.var("Deco_WJets0_sb_lo_sim_%s_%s_mlvj_eig3"%(self.channel, self.wtagger_label)) );
                #TTbar use exp
                self.workspace4limit_.var("Deco_TTbar_signal_region_%s_%s_mlvj_eig0"%(self.channel, self.wtagger_label)).setError(shape_para_error_TTbar);
                #self.workspace4limit_.var("Deco_TTbar_signal_region_%s_mlvj_eig1"%(self.channel)).setError(shape_para_error_TTbar);
                params_list.append(self.workspace4limit_.var("Deco_TTbar_signal_region_%s_%s_mlvj_eig0"%(self.channel, self.wtagger_label)));
                #params_list.append(self.workspace4limit_.var("Deco_TTbar_signal_region_%s_mlvj_eig1"%(self.channel)));
                #if options.closuretest==0:
                # self.FloatingParams.add(self.workspace4limit_.var("Deco_TTbar_signal_region_%s_mlvj_eig0"%(self.channel)));
                # self.FloatingParams.add(self.workspace4limit_.var("Deco_TTbar_signal_region_%s_mlvj_eig1"%(self.channel)));

        #add signal shape parameters' uncertainty
        if self.workspace4limit_.var("rrv_mean_voig_%s_signal_region_%s_%s"%(self.signal_sample, self.channel, self.wtagger_label)):
            self.workspace4limit_.var("rrv_mean_voig_%s_signal_region_%s_%s"%(self.signal_sample, self.channel, self.wtagger_label)).setError( ( self.workspace4limit_.var("rrv_mean_voig_%s_signal_region_%s_%s"%(self.signal_sample, self.channel, self.wtagger_label)).getError()**2 + (self.workspace4limit_.var("rrv_mean_voig_%s_signal_region_%s_%s"%(self.signal_sample, self.channel, self.wtagger_label)).getVal()*0.013)**2 )**0.5 );
            self.workspace4limit_.var("rrv_sigma_voig_%s_signal_region_%s_%s"%(self.signal_sample, self.channel, self.wtagger_label)).setError( (self.workspace4limit_.var("rrv_sigma_voig_%s_signal_region_%s_%s"%(self.signal_sample, self.channel, self.wtagger_label)).getError()**2 + (self.workspace4limit_.var("rrv_sigma_voig_%s_signal_region_%s_%s"%(self.signal_sample, self.channel, self.wtagger_label)).getVal()*0.045)**2 )**0.5 );
            params_list.append(self.workspace4limit_.var("rrv_mean_voig_%s_signal_region_%s_%s"%(self.signal_sample, self.channel, self.wtagger_label)) );
            params_list.append(self.workspace4limit_.var("rrv_sigma_voig_%s_signal_region_%s_%s"%(self.signal_sample, self.channel, self.wtagger_label)) );
        if self.workspace4limit_.var("rrv_mean_CB_%s_signal_region_%s_%s"%(self.signal_sample, self.channel, self.wtagger_label)):
            self.workspace4limit_.var("rrv_mean_CB_%s_signal_region_%s_%s"%(self.signal_sample, self.channel, self.wtagger_label)).setError( ( self.workspace4limit_.var("rrv_mean_CB_%s_signal_region_%s_%s"%(self.signal_sample, self.channel, self.wtagger_label)).getError()**2 + (self.workspace4limit_.var("rrv_mean_CB_%s_signal_region_%s_%s"%(self.signal_sample, self.channel, self.wtagger_label)).getVal()*0.013)**2 )**0.5 );
            self.workspace4limit_.var("rrv_sigma_CB_%s_signal_region_%s_%s"%(self.signal_sample, self.channel, self.wtagger_label)).setError( ( self.workspace4limit_.var("rrv_sigma_CB_%s_signal_region_%s_%s"%(self.signal_sample, self.channel, self.wtagger_label)).getError()**2 + (self.workspace4limit_.var("rrv_sigma_CB_%s_signal_region_%s_%s"%(self.signal_sample, self.channel, self.wtagger_label)).getVal()*0.045)**2 )**0.5 );
            params_list.append(self.workspace4limit_.var("rrv_mean_CB_%s_signal_region_%s_%s"%(self.signal_sample, self.channel, self.wtagger_label)) );
            params_list.append(self.workspace4limit_.var("rrv_sigma_CB_%s_signal_region_%s_%s"%(self.signal_sample, self.channel, self.wtagger_label)) );


        getattr(self.workspace4limit_,"import")(self.FloatingParams);
 
        self.save_workspace_to_file();
        #calculate the shape uncertainty for cut-and-countingd
        
        self.rrv_counting_uncertainty_from_shape_uncertainty=RooRealVar("rrv_counting_uncertainty_from_shape_uncertainty_%s"%(self.channel),"rrv_counting_uncertainty_from_shape_uncertainty_%s"%(self.channel),0);
        self.rrv_counting_uncertainty_from_shape_uncertainty.setError( Calc_error("WJets_%s"%(self.channel), "rrv_mass_lvj" ,self.FloatingParams,self.workspace4limit_,"signal_region") );
        self.rrv_counting_uncertainty_from_shape_uncertainty.Print();

        self.print_limit_datacard("unbin",params_list);
        self.print_limit_datacard("counting");

        
    ######### ++++++++++++++
    def read_workspace(self):
        file = TFile(self.file_rlt_root) ;
        workspace = file.Get("workspace4limit_") ;
        workspace.Print()

        parameters_workspace=workspace.allVars();
        par=parameters_workspace.createIterator();
        par.Reset();
        param=par.Next()
        while (param):
            param.Print();
            param=par.Next()
        print "___________________________________________________"

        workspace.data("data_obs_%s"%(self.channel)).Print()
        print "___________________________________________________"
        pdfs_workspace=workspace.allPdfs();
        par=pdfs_workspace.createIterator();
        par.Reset();
        param=par.Next()
        while (param):
            param.Print();
            param=par.Next()
        print "___________________________________________________"

        rrv_x=workspace.var("rrv_mass_lvj")
        data_obs=workspace.data("data_obs_%s"%(self.channel))
        model_pdf_signal=workspace.pdf("%s_%s"%(self.signal_sample,self.channel))
        model_pdf_WJets=workspace.pdf("WJets_%s"%(self.channel))
        model_pdf_VV=workspace.pdf("VV_%s"%(self.channel))
        model_pdf_TTbar=workspace.pdf("TTbar_%s"%(self.channel))
        model_pdf_STop=workspace.pdf("STop_%s"%(self.channel))

        model_pdf_signal.Print();
        model_pdf_WJets.Print();
        model_pdf_VV.Print();
        model_pdf_TTbar.Print();
        model_pdf_STop.Print();

        rrv_number_signal=workspace.var("rate_%s_for_unbin"%(self.signal_sample))
        rrv_number_WJets=workspace.var("rate_WJets_for_unbin")
        rrv_number_VV=workspace.var("rate_VV_for_unbin")
        rrv_number_TTbar=workspace.var("rate_TTbar_for_unbin")
        rrv_number_STop=workspace.var("rate_STop_for_unbin")

        rrv_number_signal.Print();
        rrv_number_WJets.Print();
        rrv_number_VV.Print();
        rrv_number_TTbar.Print();
        rrv_number_STop.Print();

        rrv_number_Total_background_MC = RooRealVar("rrv_number_Total_background_MC","rrv_number_Total_background_MC",
                rrv_number_WJets.getVal()+
                rrv_number_VV.getVal()+
                rrv_number_TTbar.getVal()+
                rrv_number_STop.getVal());
        rrv_number_Total_background_MC.setError(TMath.Sqrt(
                rrv_number_WJets.getError()* rrv_number_WJets.getError()+
                rrv_number_VV.getError()* rrv_number_VV.getError()+
                rrv_number_TTbar.getError()* rrv_number_TTbar.getError()+
                rrv_number_STop.getError() *rrv_number_STop.getError() 
                ));
        #rrv_number_Total_background_MC.setError(0.);#we are not only care about the shape uncertainty, but also the rate uncertainty
        model_Total_background_MC = RooAddPdf("model_Total_background_MC","model_Total_background_MC",RooArgList(model_pdf_WJets,model_pdf_VV,model_pdf_TTbar,model_pdf_STop),RooArgList(rrv_number_WJets,rrv_number_VV,rrv_number_TTbar,rrv_number_STop));

        scale_number_signal=rrv_number_signal.getVal()/data_obs.sumEntries()
        scale_number_Total_background_MC=rrv_number_Total_background_MC.getVal()/data_obs.sumEntries()

        mplot=rrv_x.frame(RooFit.Title("check_workspace"), RooFit.Bins(int(rrv_x.getBins()/self.narrow_factor)));
        #data_obs.plotOn(mplot ,RooFit.DataError(RooAbsData.SumW2), RooFit.Name("data_invisible"),RooFit.Invisible());
        data_obs.plotOn(mplot , RooFit.Name("data_invisible"), RooFit.MarkerSize(1.5), RooFit.DataError(RooAbsData.SumW2), RooFit.XErrorSize(0) );

        model_Total_background_MC.plotOn(mplot,RooFit.Normalization(scale_number_Total_background_MC),RooFit.Name("WJets"), RooFit.Components("WJets_%s,VV_%s,TTbar_%s,STop_%s"%(self.channel,self.channel,self.channel,self.channel)),RooFit.DrawOption("F"), RooFit.FillColor(self.color_palet["WJets"]), RooFit.LineColor(kBlack), RooFit.VLines());
        model_Total_background_MC.plotOn(mplot,RooFit.Normalization(scale_number_Total_background_MC),RooFit.Name("VV"), RooFit.Components("VV_%s,TTbar_%s,STop_%s"%(self.channel,self.channel,self.channel)),RooFit.DrawOption("F"), RooFit.FillColor(self.color_palet["VV"]), RooFit.LineColor(kBlack), RooFit.VLines());
        model_Total_background_MC.plotOn(mplot,RooFit.Normalization(scale_number_Total_background_MC),RooFit.Name("TTbar"), RooFit.Components("TTbar_%s,STop_%s"%(self.channel,self.channel)),RooFit.DrawOption("F"), RooFit.FillColor(self.color_palet["TTbar"]), RooFit.LineColor(kBlack), RooFit.VLines());
        model_Total_background_MC.plotOn(mplot,RooFit.Normalization(scale_number_Total_background_MC),RooFit.Name("STop"), RooFit.Components("STop_%s"%(self.channel)),RooFit.DrawOption("F"), RooFit.FillColor(self.color_palet["STop"]), RooFit.LineColor(kBlack), RooFit.VLines());
        #solid line
        model_Total_background_MC.plotOn(mplot,RooFit.Normalization(scale_number_Total_background_MC),RooFit.Name("WJets_line_invisible"), RooFit.Components("WJets_%s,VV_%s,TTbar_%s,STop_%s"%(self.channel,self.channel,self.channel,self.channel)), RooFit.LineColor(kBlack), RooFit.LineWidth(2), RooFit.VLines());
        model_Total_background_MC.plotOn(mplot,RooFit.Normalization(scale_number_Total_background_MC),RooFit.Name("VV_line_invisible"), RooFit.Components("VV_%s,TTbar_%s,STop_%s"%(self.channel,self.channel,self.channel)), RooFit.LineColor(kBlack), RooFit.LineWidth(2), RooFit.VLines());
        model_Total_background_MC.plotOn(mplot,RooFit.Normalization(scale_number_Total_background_MC),RooFit.Name("TTbar_line_invisible"), RooFit.Components("TTbar_%s,STop_%s"%(self.channel,self.channel)), RooFit.LineColor(kBlack), RooFit.LineWidth(2), RooFit.VLines());
        model_Total_background_MC.plotOn(mplot,RooFit.Normalization(scale_number_Total_background_MC),RooFit.Name("STop_line_invisible"), RooFit.Components("STop_%s"%(self.channel)), RooFit.LineColor(kBlack), RooFit.LineWidth(2), RooFit.VLines());

        label_tstring=TString(self.signal_sample);
        if label_tstring.Contains("600") and (not label_tstring.Contains("1600")):
            signal_scale=20;
        elif label_tstring.Contains("700") and (not label_tstring.Contains("1700")):
            signal_scale=20;            
        elif label_tstring.Contains("800") and (not label_tstring.Contains("1800")):
            signal_scale=20;
        else:
            signal_scale=100;
        
        model_pdf_signal.plotOn(mplot,RooFit.Normalization(scale_number_signal*signal_scale),RooFit.Name("%s #times %s"%(self.signal_sample, signal_scale)),RooFit.DrawOption("L"), RooFit.LineColor(self.color_palet["Signal"]), RooFit.LineStyle(2), RooFit.VLines());
        data_obs.plotOn(mplot, RooFit.Name("data"), RooFit.MarkerSize(1.5), RooFit.DataError(RooAbsData.SumW2), RooFit.XErrorSize(0) );
        model_Total_background_MC.plotOn(mplot,RooFit.Normalization(scale_number_Total_background_MC),RooFit.Invisible());
        mplot_pull=self.get_pull(rrv_x,mplot);
        
        #floatpara_list=workspace.FindObject("floatpara_list");
        self.FloatingParams.Print("v");
        if options.closuretest==0:
            draw_error_band(model_Total_background_MC, rrv_x.GetName(), rrv_number_Total_background_MC,self.FloatingParams,workspace ,mplot,self.color_palet["Uncertainty"],"F");
        else:
            draw_error_band(model_Total_background_MC, rrv_x.GetName(), rrv_number_Total_background_MC,self.FloatingParams,workspace ,mplot,self.color_palet["Uncertainty"],"F");

        mplot.Print();
        leg=self.legend4Plot(mplot,0, 1,0.05,0,0.1 );
        mplot.addObject(leg);
        mplot.GetYaxis().SetRangeUser(1e-2,mplot.GetMaximum()*1.5);

        parameters_list=RooArgList();
        self.draw_canvas_with_pull( mplot, mplot_pull,parameters_list,"plots_%s_%s_%s_%s/m_lvj_fitting/"%(options.additioninformation, self.channel,self.PS_model,self.wtagger_label),"check_workspace_for_limit","",0,1);
        if workspace.var("rrv_num_floatparameter_in_last_fitting"):   self.nPar_float_in_fitTo= int(workspace.var("rrv_num_floatparameter_in_last_fitting").getVal());
        else:
            self.nPar_float_in_fitTo=1;
        nBinX=mplot.GetNbinsX();
        ndof= nBinX-self.nPar_float_in_fitTo; 
        print "nPar=%s, chiSquare=%s/%s"%(self.nPar_float_in_fitTo, mplot.chiSquare( self.nPar_float_in_fitTo )*ndof, ndof );

    ######## ++++++++++++++
    def save_workspace_to_file(self):
        self.workspace4limit_.writeToFile(self.file_rlt_root);
        self.file_out.close()

    ######## ++++++++++++++
    def get_pull(self, rrv_x, mplot_orig):
      hpull=mplot_orig.pullHist();
      mplot_pull = rrv_x.frame(RooFit.Title("Pull Distribution"), RooFit.Bins(int(rrv_x.getBins()/self.narrow_factor)));
      medianLine = TLine(rrv_x.getMin(),0.,rrv_x.getMax(),0); medianLine.SetLineWidth(2); medianLine.SetLineColor(kRed);
      mplot_pull.addObject(medianLine);
      mplot_pull.addPlotable(hpull,"P");
      mplot_pull.SetTitle("PULL");
      mplot_pull.GetXaxis().SetTitle("");
      mplot_pull.GetYaxis().SetTitle("(Data-Fit)/#sigma_{Data}");
      mplot_pull.SetTitle("PULL");
      mplot_pull.GetYaxis().SetRangeUser(-5,5);
      mplot_pull.GetYaxis().SetTitleSize(0.10);
      mplot_pull.GetYaxis().SetLabelSize(0.10);
      mplot_pull.GetXaxis().SetTitleSize(0.10);
      mplot_pull.GetXaxis().SetLabelSize(0.10);
      return mplot_pull;
                                                                                    

    ######## ++++++++++++++
    def banner4Plot(self,iswithpull=0):
        if iswithpull:
          if self.channel=="el":
              banner = TLatex(0.26,0.96,("CMS Preliminary, %.1f fb^{-1} at #sqrt{s} = 8 TeV, W#rightarrow e #nu %s"%(self.GetLumi(),self.wtagger_label)));
          if self.channel=="mu":
              banner = TLatex(0.26,0.96,("CMS Preliminary, %.1f fb^{-1} at #sqrt{s} = 8 TeV, W#rightarrow #mu #nu %s"%(self.GetLumi(),self.wtagger_label)));
          banner.SetNDC(); banner.SetTextSize(0.035);
        else:
          if self.channel=="el":
              banner = TLatex(0.3,0.96,("CMS Preliminary, %.1f fb^{-1} at #sqrt{s} = 8 TeV, W#rightarrow e #nu %s"%(self.GetLumi(),self.wtagger_label)));
          if self.channel=="mu":
              banner = TLatex(0.3,0.96,("CMS Preliminary, %.1f fb^{-1} at #sqrt{s} = 8 TeV, W#rightarrow #mu #nu %s"%(self.GetLumi(),self.wtagger_label)));
          banner.SetNDC(); banner.SetTextSize(0.029);

        return banner;
                                             
    ######## ++++++++++++++
    def legend4Plot(self, plot, left=1, isFill=1, xoffset=0., yoffset=0., x_right_offset=0., y_upper_offset=0.):
        if left==-1:
            theLeg = TLegend(0.65+xoffset, 0.57+yoffset, 0.92+xoffset, 0.87+yoffset, "", "NDC");
            theLeg.SetName("theLegend");
            theLeg.SetBorderSize(0);
            theLeg.SetLineColor(0);
            theLeg.SetFillColor(0);
            if isFill:
                theLeg.SetFillStyle(1001);
            else:
                theLeg.SetFillStyle(0);
            theLeg.SetLineWidth(0);
            theLeg.SetLineStyle(0);
            theLeg.SetTextFont(42);
            theLeg.SetTextSize(.04);
            #theLeg.SetTextSize(.045);
        else:
#            theLeg = TLegend(0.47+xoffset, 0.66+yoffset, 0.76+xoffset+x_right_offset, 0.93+yoffset+y_upper_offset, "", "NDC");
            theLeg = TLegend(0.41+xoffset, 0.6+yoffset, 0.76+xoffset+x_right_offset, 0.93+yoffset+y_upper_offset, "", "NDC");
            theLeg.SetFillColor(0);
            if isFill:
                theLeg.SetFillStyle(0);
            else:
                theLeg.SetFillStyle(0);
            theLeg.SetNColumns(2);
        theLeg.SetBorderSize(0);
        theLeg.SetLineColor(0);
        theLeg.SetLineWidth(0);
        theLeg.SetLineStyle(0);

        entryCnt = 0;
        objName_before = "";
        objName_signal_graviton = "";
        objNameLeg_signal_graviton = "";
        
	for obj in range(int(plot.numItems()) ):
            objName = plot.nameOf(obj);
            print objName;
            if not ( ( (plot.getInvisible(objName)) and (not TString(objName).Contains("Uncertainty")) ) or TString(objName).Contains("invisi") or TString(objName).Contains("TLine") or 
objName ==objName_before ):
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
                    elif TString(objName).Data()=="VV" : theLeg.AddEntry(theObj, "WW/WZ/ZZ","F");
                    elif TString(objName).Data()=="WJets" : theLeg.AddEntry(theObj, "W+jets","F");
                    elif TString(objName).Contains("vbfH"): theLeg.AddEntry(theObj, (TString(objName).ReplaceAll("vbfH","qqH")).Data() ,"L");
                    elif TString(objName).Contains("Uncertainty"): theLeg.AddEntry(theObj, objTitle,drawoption);
                    elif TString(objName).Contains("Bulk"):
                       if TString(objName).Contains("M600"): objName_signal_graviton=theObj ;  objNameLeg_signal_graviton = TString(objName).ReplaceAll("BulkG_c0p2_M600 #times 100","Bulk G, M=0.6 TeV ( #times 100)").Data()
                       if TString(objName).Contains("M700"): objName_signal_graviton=theObj ;  objNameLeg_signal_graviton = TString(objName).ReplaceAll("BulkG_c0p2_M700 #times 100","Bulk G, M=0.7 TeV ( #times 100)").Data()
                       if TString(objName).Contains("M800"): objName_signal_graviton=theObj ;  objNameLeg_signal_graviton = TString(objName).ReplaceAll("BulkG_c0p2_M800 #times 100","Bulk G, M=0.8 TeV ( #times 100)").Data()
                       if TString(objName).Contains("M900"): objName_signal_graviton=theObj ;  objNameLeg_signal_graviton = TString(objName).ReplaceAll("BulkG_c0p2_M900 #times 100","Bulk G, M=0.9 TeV ( #times 100)").Data()
                       if TString(objName).Contains("M1000"): objName_signal_graviton=theObj ;  objNameLeg_signal_graviton = TString(objName).ReplaceAll("BulkG_c0p2_M1000 #times 100","Bulk G, M=1.0 TeV ( #times 100)").Data()
                       if TString(objName).Contains("M1100"): objName_signal_graviton=theObj ;  objNameLeg_signal_graviton = TString(objName).ReplaceAll("BulkG_c0p2_M1100 #times 100","Bulk G, M=1.1 TeV ( #times 100)").Data()
                       if TString(objName).Contains("M1200"): objName_signal_graviton=theObj ;  objNameLeg_signal_graviton = TString(objName).ReplaceAll("BulkG_c0p2_M1200 #times 100","Bulk G, M=1.2 TeV ( #times 100)").Data()
                       if TString(objName).Contains("M1300"): objName_signal_graviton=theObj ;  objNameLeg_signal_graviton = TString(objName).ReplaceAll("BulkG_c0p2_M1300 #times 100","Bulk G, M=1.3 TeV ( #times 100)").Data()
                       if TString(objName).Contains("M1400"): objName_signal_graviton=theObj ;  objNameLeg_signal_graviton = TString(objName).ReplaceAll("BulkG_c0p2_M1400 #times 100","Bulk G, M=1.4 TeV ( #times 100)").Data()
                       if TString(objName).Contains("M1500"): objName_signal_graviton=theObj ;  objNameLeg_signal_graviton = TString(objName).ReplaceAll("BulkG_c0p2_M1500 #times 100","Bulk G, M=1.5 TeV ( #times 100)").Data()
                       if TString(objName).Contains("M1600"): objName_signal_graviton=theObj ;  objNameLeg_signal_graviton = TString(objName).ReplaceAll("BulkG_c0p2_M1600 #times 100","Bulk G, M=1.6 TeV ( #times 100)").Data()
                       if TString(objName).Contains("M1700"): objName_signal_graviton=theObj ;  objNameLeg_signal_graviton = TString(objName).ReplaceAll("BulkG_c0p2_M1700 #times 100","Bulk G, M=1.7 TeV ( #times 100)").Data()
                       if TString(objName).Contains("M1800"): objName_signal_graviton=theObj ;  objNameLeg_signal_graviton = TString(objName).ReplaceAll("BulkG_c0p2_M1800 #times 100","Bulk G, M=1.8 TeV ( #times 100)").Data()
                       if TString(objName).Contains("M1900"): objName_signal_graviton=theObj ;  objNameLeg_signal_graviton = TString(objName).ReplaceAll("BulkG_c0p2_M1900 #times 100","Bulk G, M=1.9 TeV ( #times 100)").Data()
                       if TString(objName).Contains("M2000"): objName_signal_graviton=theObj ;  objNameLeg_signal_graviton = TString(objName).ReplaceAll("BulkG_c0p2_M2000 #times 100","Bulk G, M=2.0 TeV ( #times 100)").Data()
                       if TString(objName).Contains("M2100"): objName_signal_graviton=theObj ;  objNameLeg_signal_graviton = TString(objName).ReplaceAll("BulkG_c0p2_M2100 #times 100","Bulk G, M=2.1 TeV ( #times 100)").Data()
                       if TString(objName).Contains("M2200"): objName_signal_graviton=theObj ;  objNameLeg_signal_graviton = TString(objName).ReplaceAll("BulkG_c0p2_M2200 #times 100","Bulk G, M=2.2 TeV ( #times 100)").Data()
                       if TString(objName).Contains("M2300"): objName_signal_graviton=theObj ;  objNameLeg_signal_graviton = TString(objName).ReplaceAll("BulkG_c0p2_M2300 #times 100","Bulk G, M=2.3 TeV ( #times 100)").Data()
                       if TString(objName).Contains("M2400"): objName_signal_graviton=theObj ;  objNameLeg_signal_graviton = TString(objName).ReplaceAll("BulkG_c0p2_M2400 #times 100","Bulk G, M=2.4 TeV ( #times 100)").Data()
                       if TString(objName).Contains("M2500"): objName_signal_graviton=theObj ;  objNameLeg_signal_graviton = TString(objName).ReplaceAll("BulkG_c0p2_M2500 #times 100","Bulk G, M=2.5 TeV ( #times 100)").Data()
                    else : theLeg.AddEntry(theObj, objTitle,drawoption);
                entryCnt=entryCnt+1;
            objName_before=objName;
        if objName_signal_graviton !="" :
           theLeg.AddEntry(objName_signal_graviton, TString(objNameLeg_signal_graviton).Data() ,"L");
        return theLeg;

    ######## ++++++++++++++
    def draw_canvas_with_pull(self, mplot, mplot_pull,parameters_list,in_directory, in_file_name, in_model_name="", show_constant_parameter=0, logy=0):# mplot + pull + parameters

        mplot.GetXaxis().SetTitleOffset(1.1);
        mplot.GetYaxis().SetTitleOffset(1.3);
        mplot.GetXaxis().SetTitleSize(0.05);
        mplot.GetYaxis().SetTitleSize(0.05);
        mplot.GetXaxis().SetLabelSize(0.045);
        mplot.GetYaxis().SetLabelSize(0.045);
        mplot_pull.GetXaxis().SetLabelSize(0.15);
        mplot_pull.GetYaxis().SetLabelSize(0.15);
        mplot_pull.GetYaxis().SetTitleSize(0.15);
        mplot_pull.GetYaxis().SetTitle("(Data-Fit)/#sigma_{Data}");
        mplot_pull.GetYaxis().SetNdivisions(205);

        cMassFit = TCanvas("cMassFit","cMassFit", 600,600);
        # if parameters_list is empty, don't draw pad3
        par_first=parameters_list.createIterator();
        par_first.Reset();
        param_first=par_first.Next()
        doParameterPlot = 0 ;
        if param_first and doParameterPlot != 0:
            pad1=TPad("pad1","pad1",0.,0. ,0.8,0.24);
            pad2=TPad("pad2","pad2",0.,0.24,0.82,1. );
            pad3=TPad("pad3","pad3",0.82,0.,1,1);
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
        banner = self.banner4Plot(1); banner.Draw();

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


        Directory=TString(in_directory+self.signal_sample+"_%02d_%02d/"%(options.cprime,options.BRnew));
        if not Directory.EndsWith("/"):Directory=Directory.Append("/");
        if not os.path.isdir(Directory.Data()): os.system("mkdir -p "+Directory.Data());

        rlt_file=TString(Directory.Data()+in_file_name);
        if rlt_file.EndsWith(".root"):
            rlt_file.ReplaceAll(".root","_"+in_model_name+"_with_pull.png");
        else:
            rlt_file=rlt_file.Append("_"+in_model_name+"_with_pull.png");
        cMassFit.SaveAs(rlt_file.Data());
        rlt_file.ReplaceAll(".png",".pdf");
        cMassFit.SaveAs(rlt_file.Data());

        string_file_name=TString(in_file_name);
        if string_file_name.EndsWith(".root"): string_file_name.ReplaceAll(".root","_"+in_model_name);
        else: rlt_file.Append(in_model_name);
        if logy:
            pad2.cd();
            mplot.GetYaxis().SetRangeUser(1e-2,mplot.GetMaximum()*10);
            mplot.Draw();
            pad2.SetLogy() ;
            pad2.Update();
            cMassFit.Update();
            rlt_file.ReplaceAll(".pdf","_log.pdf");
            cMassFit.SaveAs(rlt_file.Data());
            rlt_file.ReplaceAll(".pdf",".png");
            cMassFit.SaveAs(rlt_file.Data());
            mplot.GetYaxis().SetRangeUser(1e-2,mplot.GetMaximum()/10);

        self.draw_canvas(mplot,in_directory,string_file_name.Data(),0,logy,1);

    ######## ++++++++++++++
    def draw_canvas(self, in_obj,in_directory, in_file_name, is_range=0, logy=0, withpull=0):
        cMassFit = TCanvas("cMassFit","cMassFit", 600,600);
        if is_range:
            h2=TH2D("h2","",100,400,1400,4,0.00001,4); h2.Draw(); in_obj.Draw("same")
        else :
            in_obj.Draw()

        if not withpull :
          in_obj.GetXaxis().SetTitleSize(0.05);
          in_obj.GetXaxis().SetTitleOffset(1.05);
          in_obj.GetXaxis().SetLabelSize(0.042);

          in_obj.GetYaxis().SetTitleSize(0.05);
          in_obj.GetYaxis().SetTitleOffset(1.45);
          in_obj.GetYaxis().SetLabelSize(0.042);

        else:
          in_obj.GetXaxis().SetTitleSize(0.05);
          in_obj.GetXaxis().SetTitleOffset(0.95);
          in_obj.GetXaxis().SetLabelSize(0.045);

          in_obj.GetYaxis().SetTitleSize(0.05);
          in_obj.GetYaxis().SetTitleOffset(1.20);
          in_obj.GetYaxis().SetLabelSize(0.045);


        if not withpull: banner = self.banner4Plot(); banner.Draw();

        Directory=TString(in_directory+self.signal_sample+"_%02d_%02d/"%(options.cprime,options.BRnew));
        if not Directory.EndsWith("/"):Directory=Directory.Append("/");
        if not os.path.isdir(Directory.Data()): os.system("mkdir -p "+Directory.Data());

        rlt_file=TString(Directory.Data()+in_file_name);
        if rlt_file.EndsWith(".root"):
            rlt_file.ReplaceAll(".root","_rlt_without_pull_and_paramters.png");
        else:
            #rlt_file=rlt_file.Append("_rlt_without_pull_and_paramters.png");
            rlt_file=rlt_file.Append(".png");
        cMassFit.SaveAs(rlt_file.Data());
        rlt_file.ReplaceAll(".png",".pdf");
        cMassFit.SaveAs(rlt_file.Data());

        if logy:
            in_obj.GetYaxis().SetRangeUser(1e-2,in_obj.GetMaximum()*10);
            in_obj.Draw();
            cMassFit.SetLogy() ;
            cMassFit.Update();
            rlt_file.ReplaceAll(".pdf","_log.pdf");
            cMassFit.SaveAs(rlt_file.Data());
            rlt_file.ReplaceAll(".pdf",".png");
            cMassFit.SaveAs(rlt_file.Data());

    ######## ++++++++++++++
    def GetLumi(self):
        if self.channel=="el": return 19.3#5.1#19.2#13.9;
        if self.channel=="mu": return 19.3#5.3#19.3#14.0;


    ######## ++++++++++++++
    def get_data(self):
        print "get_data"
        self.get_mj_and_mlvj_dataset(self.file_data,"_data")
        getattr(self.workspace4limit_,"import")(self.workspace4fit_.var("rrv_number_dataset_signal_region_data_%s_mlvj"%(self.channel)).clone("observation_for_counting"))
 
    ######## ++++++++++++++
    def fit_Signal(self):
        print "fit_Signal"

        self.get_mj_and_mlvj_dataset(self.file_signal,"_%s"%(self.signal_sample))# to get the shape of m_lvj
        self.fit_mj_single_MC(self.file_signal,"_%s"%(self.signal_sample),"2Gaus");
    
        if TString(self.signal_sample).Contains("600") and (not TString(self.signal_sample).Contains("1600") ):
           self.fit_mlvj_model_single_MC(self.file_signal,"_%s"%(self.signal_sample),"_signal_region","Voig_v2", 0, 0, 1);
        elif TString(self.signal_sample).Contains("700") and (not TString(self.signal_sample).Contains("1700") ):
           self.fit_mlvj_model_single_MC(self.file_signal,"_%s"%(self.signal_sample),"_signal_region","Voig_v2", 0, 0, 1);
        elif TString(self.signal_sample).Contains("800") and (not TString(self.signal_sample).Contains("1800") ):
           self.fit_mlvj_model_single_MC(self.file_signal,"_%s"%(self.signal_sample),"_signal_region","Voig_v2", 0, 0, 1);
        elif TString(self.signal_sample).Contains("900") and (not TString(self.signal_sample).Contains("1900") ):
           self.fit_mlvj_model_single_MC(self.file_signal,"_%s"%(self.signal_sample),"_signal_region","Voig_v2", 0, 0, 1);
        elif TString(self.signal_sample).Contains("1000") :
           self.fit_mlvj_model_single_MC(self.file_signal,"_%s"%(self.signal_sample),"_signal_region","Voig_v2", 0, 0, 1);
        else:
           self.fit_mlvj_model_single_MC(self.file_signal,"_%s"%(self.signal_sample),"_signal_region","CB_v1", 0, 0, 1);

        print "________________________________________________________________________"


    ######## ++++++++++++++
    def fit_WJets(self):
        print "fit_WJets"
        self.get_mj_and_mlvj_dataset(self.file_WJets0_mc,"_WJets0")# to get the shape of m_lvj
        self.get_mj_and_mlvj_dataset(self.file_WJets1_mc,"_WJets1")# to get the shape of m_lvj
        self.get_mj_and_mlvj_dataset(self.file_WJets0_mc,"_WJets01")# to get the shape of m_lvj

        if self.MODEL_4_mlvj=="ErfPowExp_v1" or self.MODEL_4_mlvj=="ErfPow2_v1" or self.MODEL_4_mlvj=="ErfExp_v1" :
         self.fit_mj_single_MC(self.file_WJets0_mc,"_WJets0","ErfExp");
         self.fit_mj_single_MC(self.file_WJets1_mc,"_WJets1","User1");# use for estimating the PS model uncertainty
         self.fit_mj_single_MC(self.file_WJets0_mc,"_WJets01","User1");# use for estimating the fitting model uncertainty
        else:
         self.fit_mj_single_MC(self.file_WJets0_mc,"_WJets0","User1");
         self.fit_mj_single_MC(self.file_WJets1_mc,"_WJets1","User1");# use for estimating the PS model uncertainty
         self.fit_mj_single_MC(self.file_WJets0_mc,"_WJets01","ErfExp");# use for estimating the fitting model uncertainty
            
        #jet mass down and up
        self.get_mj_and_mlvj_dataset(self.file_WJets0_mc,"_WJets0massup","jet_mass_pr_up")
        self.get_mj_and_mlvj_dataset(self.file_WJets0_mc,"_WJets0massdn","jet_mass_pr_dn")
        if self.MODEL_4_mlvj=="ErfPowExp_v1" or self.MODEL_4_mlvj=="ErfPow2_v1" or self.MODEL_4_mlvj=="ErfExp_v1" :
         self.fit_mj_single_MC(self.file_WJets0_mc,"_WJets0massup","ErfExp");
         self.fit_mj_single_MC(self.file_WJets0_mc,"_WJets0massdn","ErfExp");
        else:
         self.fit_mj_single_MC(self.file_WJets0_mc,"_WJets0massup","User1");
         self.fit_mj_single_MC(self.file_WJets0_mc,"_WJets0massdn","User1");

        self.fit_mlvj_model_single_MC(self.file_WJets0_mc,"_WJets0","_sb_lo",self.MODEL_4_mlvj, 0, 0, 1, 0);
#        self.fit_mlvj_model_single_MC(self.file_WJets0_mc,"_WJets0","_sb_hi",self.MODEL_4_mlvj, 0, 0, 1, 0);
        
        self.fit_mlvj_model_single_MC(self.file_WJets0_mc,"_WJets0","_signal_region",self.MODEL_4_mlvj, 0, 0, 1);

        self.fit_mlvj_model_single_MC(self.file_WJets1_mc,"_WJets1","_sb_lo",self.MODEL_4_mlvj, 0, 0, 1, 0);
#        self.fit_mlvj_model_single_MC(self.file_WJets1_mc,"_WJets1","_sb_hi",self.MODEL_4_mlvj, 0, 0, 1, 0);

        self.fit_mlvj_model_single_MC(self.file_WJets1_mc,"_WJets1","_signal_region",self.MODEL_4_mlvj, 0, 0, 1);

        self.fit_mlvj_model_single_MC(self.file_WJets0_mc,"_WJets01","_sb_lo",self.MODEL_4_mlvj_alter, 0, 0, 1, 1);
#        self.fit_mlvj_model_single_MC(self.file_WJets0_mc,"_WJets01","_sb_hi",self.MODEL_4_mlvj_alter, 0, 0, 1, 1);

        self.fit_mlvj_model_single_MC(self.file_WJets0_mc,"_WJets01","_signal_region",self.MODEL_4_mlvj_alter, 0, 0, 1);

        print "________________________________________________________________________"

    ######## ++++++++++++++
    def fit_VV(self):

        print "fit_VV"
        self.get_mj_and_mlvj_dataset(self.file_VV_mc,"_VV")# to get the shape of m_lvj
        self.get_mj_and_mlvj_dataset(self.file_VV_mc,"_VVmassup","jet_mass_pr_up")
        self.get_mj_and_mlvj_dataset(self.file_VV_mc,"_VVmassdn","jet_mass_pr_dn")

        if self.MODEL_4_mlvj=="ErfPowExp_v1" or self.MODEL_4_mlvj=="ErfPow2_v1" or self.MODEL_4_mlvj=="ErfExp_v1":
         if self.wtagger_label=="LP" :
          self.fit_mj_single_MC(self.file_VV_mc,"_VV","ExpGaus");
          self.fit_mj_single_MC(self.file_VV_mc,"_VVmassup","ExpGaus");
          self.fit_mj_single_MC(self.file_VV_mc,"_VVmassdn","ExpGaus");
         else:
          self.fit_mj_single_MC(self.file_VV_mc,"_VV","2_2Gaus");
          self.fit_mj_single_MC(self.file_VV_mc,"_VVmassup","2_2Gaus");
          self.fit_mj_single_MC(self.file_VV_mc,"_VVmassdn","2_2Gaus");
        else:
         if self.wtagger_label=="LP" :
              self.fit_mj_single_MC(self.file_VV_mc,"_VV","ExpGaus");
              self.fit_mj_single_MC(self.file_VV_mc,"_VVmassup","ExpGaus");
              self.fit_mj_single_MC(self.file_VV_mc,"_VVmassdn","ExpGaus");
         else:
              self.fit_mj_single_MC(self.file_VV_mc,"_VV","2_2Gaus");
              self.fit_mj_single_MC(self.file_VV_mc,"_VVmassup","2_2Gaus");
              self.fit_mj_single_MC(self.file_VV_mc,"_VVmassdn","2_2Gaus");

        if self.MODEL_4_mlvj=="ErfPowExp_v1" or self.MODEL_4_mlvj=="ErfPow2_v1" or self.MODEL_4_mlvj=="ErfExp_v1":
            self.fit_mlvj_model_single_MC(self.file_VV_mc,"_VV","_sb_lo","ErfExp_v1", 0, 0, 1, 0);
  #          self.fit_mlvj_model_single_MC(self.file_VV_mc,"_VV","_sb_hi","ErfExp_v1", 0, 0, 1, 0);
            self.fit_mlvj_model_single_MC(self.file_VV_mc,"_VV","_signal_region",self.MODEL_4_mlvj, 0, 0, 1);
         
        else:
            self.fit_mlvj_model_single_MC(self.file_VV_mc,"_VV","_sb_lo","Exp", 0, 0, 1, 0);
 #           self.fit_mlvj_model_single_MC(self.file_VV_mc,"_VV","_sb_hi","Exp", 0, 0, 1, 0);
            self.fit_mlvj_model_single_MC(self.file_VV_mc,"_VV","_signal_region",self.MODEL_4_mlvj, 0, 0, 1);
 
        print "________________________________________________________________________"

    ######## ++++++++++++++
    def fit_TTbar(self):

        print "fit_TTbar"

        self.get_mj_and_mlvj_dataset(self.file_TTbar_mc,"_TTbar") #to get the shape of m_lvj
        self.get_mj_and_mlvj_dataset(self.file_TTbar_matchDn_mc,"_TTbar_matchDn") #to get the shape of m_lvj
        self.get_mj_and_mlvj_dataset(self.file_TTbar_matchUp_mc,"_TTbar_matchUp") #to get the shape of m_lvj
        self.get_mj_and_mlvj_dataset(self.file_TTbar_scaleDn_mc,"_TTbar_scaleDn")# to get the shape of m_lvj
        self.get_mj_and_mlvj_dataset(self.file_TTbar_scaleUp_mc,"_TTbar_scaleUp")# to get the shape of m_lvj
        self.get_mj_and_mlvj_dataset(self.file_TTbar_MG_mc,"_TTbar_MG")# to get the shape of m_lvj
        self.get_mj_and_mlvj_dataset(self.file_TTbar_mc,"_TTbarmassup","jet_mass_pr_up")
        self.get_mj_and_mlvj_dataset(self.file_TTbar_mc,"_TTbarmassdn","jet_mass_pr_dn")

        if self.MODEL_4_mlvj=="ErfPowExp_v1" or self.MODEL_4_mlvj=="ErfPow2_v1" or self.MODEL_4_mlvj=="ErfExp_v1":
         if self.wtagger_label== "LP" :
           self.fit_mj_single_MC(self.file_TTbar_mc,"_TTbar","ExpGaus");
           self.fit_mj_single_MC(self.file_TTbar_mc,"_TTbarmassup","ExpGaus");
           self.fit_mj_single_MC(self.file_TTbar_mc,"_TTbarmassdn","ExpGaus");
         else:
           self.fit_mj_single_MC(self.file_TTbar_mc,"_TTbar","2Gaus_ErfExp");
           self.fit_mj_single_MC(self.file_TTbar_mc,"_TTbarmassup","2Gaus_ErfExp");
           self.fit_mj_single_MC(self.file_TTbar_mc,"_TTbarmassdn","2Gaus_ErfExp");
        else:
           if self.wtagger_label== "LP" :
               self.fit_mj_single_MC(self.file_TTbar_mc,"_TTbar","ExpGaus");
               self.fit_mj_single_MC(self.file_TTbar_mc,"_TTbarmassup","ExpGaus");
               self.fit_mj_single_MC(self.file_TTbar_mc,"_TTbarmassdn","ExpGaus");
           else:
               self.fit_mj_single_MC(self.file_TTbar_mc,"_TTbar","2Gaus_ErfExp");
               self.fit_mj_single_MC(self.file_TTbar_mc,"_TTbarmassup","2Gaus_ErfExp");
               self.fit_mj_single_MC(self.file_TTbar_mc,"_TTbarmassdn","2Gaus_ErfExp");
        
   
        if self.MODEL_4_mlvj=="ErfPowExp_v1" or self.MODEL_4_mlvj=="ErfPow2_v1" or self.MODEL_4_mlvj=="ErfExp_v1" :
            self.fit_mlvj_model_single_MC(self.file_TTbar_mc,"_TTbar","_sb_lo","ErfExp_v1", 0, 0, 1, 0);
   #         self.fit_mlvj_model_single_MC(self.file_TTbar_mc,"_TTbar","_sb_hi","ErfExp_v1", 0, 0, 1, 0);
            self.fit_mlvj_model_single_MC(self.file_TTbar_matchDn_mc,"_TTbar_matchDn","_signal_region",self.MODEL_4_mlvj, 0, 0, 1);
            self.fit_mlvj_model_single_MC(self.file_TTbar_matchUp_mc,"_TTbar_matchUp","_signal_region",self.MODEL_4_mlvj, 0, 0, 1);
            self.fit_mlvj_model_single_MC(self.file_TTbar_scaleDn_mc,"_TTbar_scaleDn","_signal_region",self.MODEL_4_mlvj, 0, 0, 1);
            self.fit_mlvj_model_single_MC(self.file_TTbar_scaleUp_mc,"_TTbar_scaleUp","_signal_region",self.MODEL_4_mlvj, 0, 0, 1);
            self.fit_mlvj_model_single_MC(self.file_TTbar_MG_mc,"_TTbar_MG","_signal_region",self.MODEL_4_mlvj);
            self.fit_mlvj_model_single_MC(self.file_TTbar_mc,"_TTbar","_signal_region",self.MODEL_4_mlvj,1, 0, 1);

        else:
            self.fit_mlvj_model_single_MC(self.file_TTbar_mc,"_TTbar","_sb_lo","Exp",0, 0, 1, 0);
    #        self.fit_mlvj_model_single_MC(self.file_TTbar_mc,"_TTbar","_sb_hi","Exp",0, 0, 1, 0);
            self.fit_mlvj_model_single_MC(self.file_TTbar_matchDn_mc,"_TTbar_matchDn","_signal_region","Exp", 0, 0, 1);
            self.fit_mlvj_model_single_MC(self.file_TTbar_matchUp_mc,"_TTbar_matchUp","_signal_region","Exp", 0, 0, 1);
            self.fit_mlvj_model_single_MC(self.file_TTbar_scaleDn_mc,"_TTbar_scaleDn","_signal_region","Exp", 0, 0, 1);
            self.fit_mlvj_model_single_MC(self.file_TTbar_scaleUp_mc,"_TTbar_scaleUp","_signal_region","Exp", 0, 0, 1);
            self.fit_mlvj_model_single_MC(self.file_TTbar_MG_mc,"_TTbar_MG","_signal_region","Exp");
            self.fit_mlvj_model_single_MC(self.file_TTbar_mc,"_TTbar","_signal_region","Exp",1, 0, 1);
 
        print "________________________________________________________________________"


    ######## ++++++++++++++
    def fit_STop(self):
        print "fit_STop"

        self.get_mj_and_mlvj_dataset(self.file_STop_mc,"_STop") #to get the shape of m_lvj
        self.get_mj_and_mlvj_dataset(self.file_STop_mc,"_STopmassup","jet_mass_pr_up")
        self.get_mj_and_mlvj_dataset(self.file_STop_mc,"_STopmassdn","jet_mass_pr_dn")

        self.fit_mj_single_MC(self.file_STop_mc,"_STop","ExpGaus");
        self.fit_mj_single_MC(self.file_STop_mc,"_STopmassup","ExpGaus");
        self.fit_mj_single_MC(self.file_STop_mc,"_STopmassdn","ExpGaus");

        if self.MODEL_4_mlvj=="ErfPowExp_v1" or self.MODEL_4_mlvj=="ErfPow2_v1" or self.MODEL_4_mlvj=="ErfExp_v1":
            self.fit_mlvj_model_single_MC(self.file_STop_mc,"_STop","_sb_lo","ErfExp_v1", 0, 0, 1, 0);
     #       self.fit_mlvj_model_single_MC(self.file_STop_mc,"_STop","_sb_hi","ErfExp_v1", 0, 0, 1, 0);
            self.fit_mlvj_model_single_MC(self.file_STop_mc,"_STop","_signal_region","ErfExp_v1", 0, 0, 1);
        else:
            self.fit_mlvj_model_single_MC(self.file_STop_mc,"_STop","_sb_lo","Exp", 0, 0, 1, 0);
     #       self.fit_mlvj_model_single_MC(self.file_STop_mc,"_STop","_sb_hi","Exp", 0, 0, 1, 0);
            self.fit_mlvj_model_single_MC(self.file_STop_mc,"_STop","_signal_region","Exp", 0, 0, 1);
        print "________________________________________________________________________"


    ######## ++++++++++++++
    def fit_AllSamples_Mj_and_Mlvj(self):
        print "fit_AllSamples_Mj_and_Mlvj"
        self.fit_WJets()
        self.fit_Signal()
        self.fit_TTbar()
        self.fit_VV()
        self.fit_STop()
        print "________________________________________________________________________"


    ####### +++++++++++++++
    def analysis_sideband_correction_method1(self):
        self.fit_AllSamples_Mj_and_Mlvj()
        self.get_data()
        self.fit_WJetsNorm();
        self.fit_mlvj_in_Mj_sideband("_WJets1","_sb_lo", self.MODEL_4_mlvj)
        self.fit_mlvj_in_Mj_sideband("_WJets01","_sb_lo", self.MODEL_4_mlvj_alter)
        self.fit_mlvj_in_Mj_sideband("_WJets0","_sb_lo", self.MODEL_4_mlvj)

      #  self.fit_mlvj_in_Mj_sideband("_WJets1","_sb_hi", self.MODEL_4_mlvj)
      #  self.fit_mlvj_in_Mj_sideband("_WJets01","_sb_hi", self.MODEL_4_mlvj_alter)
      #  self.fit_mlvj_in_Mj_sideband("_WJets0","_sb_hi", self.MODEL_4_mlvj)

        self.prepare_limit("sideband_correction_method1")
        self.read_workspace()

    ####### +++++++++++++++
    def analysis_sideband_correction_method1_without_shape_and_psmodel_systermatic(self):
        self.fit_AllSamples_Mj_and_Mlvj()
        self.get_data()
        self.fit_WJetsNormalization_in_Mj_signal_region("_WJets0");
        self.fit_mlvj_in_Mj_sideband("_WJets0","_sb_lo", self.MODEL_4_mlvj)
        self.prepare_limit("sideband_correction_method1")
        self.read_workspace()


def pre_limit_fitting_method(channel, signal_sample="BulkG_c0p2_M1000", in_mlvj_signal_region_min=500, in_mlvj_signal_region_max=700, in_mj_min=30, in_mj_max=140, in_mlvj_min=400, 
in_mlvj_max=1400):
    print "pre_limit_fitting_method for %s sample"%(channel)
    boostedW_fitter=doFit_wj_and_wlvj(channel, signal_sample, in_mlvj_signal_region_min, in_mlvj_signal_region_max, in_mj_min, in_mj_max, in_mlvj_min, in_mlvj_max)
    boostedW_fitter.analysis_fitting_method()

def pre_limit_sb_correction_without_systermatic( channel, signal_sample, in_mlvj_signal_region_min=500, in_mlvj_signal_region_max=700, in_mj_min=30, in_mj_max=140, in_mlvj_min=400, 
in_mlvj_max=1400, fit_model="ErfExp_v1", fit_model_alter="ErfPow_v1"): # the WJets M_lvj shape and normalization are from sb_correction
    boostedW_fitter=doFit_wj_and_wlvj(channel, signal_sample, in_mlvj_signal_region_min, in_mlvj_signal_region_max, in_mj_min, in_mj_max, in_mlvj_min, in_mlvj_max,fit_model, 
fit_model_alter);
    boostedW_fitter.analysis_sideband_correction_method1_without_shape_and_psmodel_systermatic()


def pre_limit_sb_correction(method, channel, signal_sample="BulkG_c0p2_M1000", in_mlvj_signal_region_min=500, in_mlvj_signal_region_max=700, in_mj_min=30, in_mj_max=140, 
in_mlvj_min=400, in_mlvj_max=1400, fit_model="ErfExp_v1", fit_model_alter="ErfPow_v1"): # the WJets M_lvj shape and normalization are from sb_correction
    print "pre_limit_sb_correction with %s for %s sample"%(method, channel)
    boostedW_fitter=doFit_wj_and_wlvj(channel, signal_sample, in_mlvj_signal_region_min, in_mlvj_signal_region_max, in_mj_min, in_mj_max, in_mlvj_min, in_mlvj_max,fit_model, 
fit_model_alter);
    #boostedW_fitter.ControlPlots();
    getattr(boostedW_fitter,"analysis_sideband_correction_%s"%(method) )();
    #getattr(boostedW_fitter,"analysis_sideband_correction_method1_without_shape_and_psmodel_systermatic")();

def control_single_sb_correction(method, channel, signal_sample="BulkG_c0p2_M1000", in_mlvj_signal_region_min=500, in_mlvj_signal_region_max=700, in_mj_min=30, in_mj_max=140, 
in_mlvj_min=400, in_mlvj_max=1400, fit_model="ErfExp_v1", fit_model_alter="ErfPow_v1"): # the WJets M_lvj shape and normalization are from sb_correction
    print "pre_limit_sb_correction with %s for %s sample"%(method, channel)
    boostedW_fitter=doFit_wj_and_wlvj(channel, signal_sample, in_mlvj_signal_region_min, in_mlvj_signal_region_max, in_mj_min, in_mj_max, in_mlvj_min, in_mlvj_max,fit_model, 
fit_model_alter);
    boostedW_fitter.ControlPlots();

def pre_limit_simple(channel):
    print "pre_limit_simple for %s sampel"%(channel)
    #pre_limit_sb_correction_without_systermatic(channel,"rsg1000_kMpl01_hw",800,1200,40,130, 800,2500,"Exp","Pow")
    #pre_limit_sb_correction_without_systermatic(channel,"BulkG_c0p2_M1000",800,1200,40,130, 700,2500,"Exp","Pow")
    #pre_limit_sb_correction_without_systermatic(channel,"BulkG_c0p2_M1600",1500,1700,40,130, 800,2800,"Exp","Pow")
    #pre_limit_sb_correction_without_systermatic(channel,"BulkG_c0p2_M2000",1900,2100,40,130, 800,3000,"Exp","Pow")
    #pre_limit_sb_correction_without_systermatic(channel,"BulkG_c0p2_M2000",1900,2100,40,130, 800,3000,"2Exp","Exp")
    #pre_limit_sb_correction_without_systermatic(channel,"BulkG_c0p2_M2000",1900,2100,40,130, 800,2800,"ExpTail","Exp")
    pre_limit_sb_correction_without_systermatic(channel,"BulkG_c0p2_M2000",1900,2100,40,130, 800,2800,"ExpN","ExpTail")
    #pre_limit_sb_correction_without_systermatic(channel,"BulkG_c0p2_M1600",1500,1700,40,130, 800,2800,"ExpN","ExpTail")
    #pre_limit_sb_correction_without_systermatic(channel,"BulkG_c0p2_M1000", 800,1200,40,130, 800,2800,"ExpN","ExpTail")

def control_single(channel):
    print "control_single for %s sampel"%(channel)
    #control_single_sb_correction("method1",channel, "BulkG_c0p2_M1000",500,700,30,140,400,1000,"ErfExp_v1")
    control_single_sb_correction("method1",channel, "BulkG_c0p2_M1000",500,1300,20,130,400,1400,"ErfExp_v1")

def check_workspace(channel, higgs):
    boostedW_fitter=doFit_wj_and_wlvj(channel,higgs); boostedW_fitter.read_workspace()

if __name__ == '__main__':
    channel=options.channel;#mu or el; default is mu;

        
    if options.control:
        print 'control for %s sample'%(channel);
        control_single(channel);

    if options.check:
        print 'check workspace for %s sample'%(channel);
        check_workspace(channel,"BulkG_c0p2_M2000");

    if options.simple and ( not options.multi) and ( not options.control) and ( not options.check):
        print 'simple mode for %s sample'%(channel)
        pre_limit_simple(channel);

    if options.multi:
        print 'multi mode for %s sample'%(channel)
        pre_limit_sb_correction("method1",sys.argv[1],sys.argv[2],int(sys.argv[3]),int(sys.argv[4]),int(sys.argv[5]),int(sys.argv[6]),int(sys.argv[7]),int(sys.argv[8]), sys.argv[9], 
sys.argv[10] )
