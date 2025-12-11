/*     */ package com.hiklife.svc;
/*     */ import java.io.IOException;
/*     */ import java.util.concurrent.CompletableFuture;
/*     */ import java.util.concurrent.TimeUnit;
/*     */ import org.bytedeco.ffmpeg.global.avcodec;
/*     */ import org.bytedeco.ffmpeg.global.avformat;
/*     */ import org.bytedeco.ffmpeg.global.avutil;
/*     */ import org.bytedeco.ffmpeg.global.swscale;
/*     */ import org.bytedeco.javacpp.Loader;
/*     */ import org.slf4j.Logger;
/*     */ import org.slf4j.LoggerFactory;

import refs.com.hiklife.svc.GetDeviceInfoClient;
import refs.com.hiklife.svc.GetDeviceInfoClientListener;
import refs.com.hiklife.svc.Kvm4JSdk;
import refs.com.hiklife.svc.SearchDeviceInfoServer;
import refs.com.hiklife.svc.SearchDeviceInfoServerListener;
import refs.com.hiklife.svc.console.KVMCInstance;
import refs.com.hiklife.svc.core.net.Connector;
import refs.com.hiklife.svc.core.protocol.ProtocolHandler;
import refs.com.hiklife.svc.core.protocol.vm.MediaType;
import refs.com.hiklife.svc.viewer.Option;
import refs.com.hiklife.svc.viewer.Viewer;
import refs.com.hiklife.svc.viewer.ViewerEvent;
import refs.com.hiklife.svc.viewer.ViewerSample;
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ public class Kvm4JSdk
/*     */ {
/*  36 */   private static final Logger log = LoggerFactory.getLogger(Kvm4JSdk.class);
/*     */ 
/*     */ 
/*     */   
/*     */   private static final String SDK_VERSION = "1.3.4.1";
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public static String getSdkVersion() {
/*  46 */     return "1.3.4.1";
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public static void startSearchDevice(int searchLocalServerUdpPort, int searchBroadcastPort, String ip, String subnetMask, SearchDeviceInfoServerListener listener) throws IOException {
/*  61 */     SearchDeviceInfoServer server = SearchDeviceInfoServer.instance();
/*  62 */     server.search(searchLocalServerUdpPort, searchBroadcastPort, ip, subnetMask, listener);
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public static void stopSearchDevice() {
/*  70 */     SearchDeviceInfoServer server = SearchDeviceInfoServer.instance();
/*  71 */     server.stop();
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public static void getDeviceInfo(String ip, int port, GetDeviceInfoClientListener listener) {
/*  83 */     (new GetDeviceInfoClient()).start(ip, port, listener);
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public static KVMCInstance connectKVMC(String ip, int port, int channelNo, String account, String password, long timeout) throws Exception {
/* 101 */     if (channelNo < 0) {
/* 102 */       throw new IllegalArgumentException("Channel index can not less than 0");
/*     */     }
/* 104 */     if (ip == null) {
/* 105 */       throw new IllegalArgumentException("ip == null");
/*     */     }
/* 107 */     if (account == null) {
/* 108 */       throw new IllegalArgumentException("account == null");
/*     */     }
/* 110 */     if (password == null) {
/* 111 */       throw new IllegalArgumentException("password == null");
/*     */     }
/* 113 */     KVMCInstance kvmcInstance = new KVMCInstance();
/* 114 */     CompletableFuture<Boolean> future = kvmcInstance.startSession(ip, port, channelNo, account, password);
/* 115 */     Boolean result = future.get(timeout, TimeUnit.MILLISECONDS);
/* 116 */     if (result.booleanValue()) {
/* 117 */       return kvmcInstance;
/*     */     }
/* 119 */     throw new Exception("Connect fail!");
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public static Viewer startSampleViewer(String ip, int port, int channelNo, ViewerEvent event) {
/* 135 */     if (channelNo < 0) {
/* 136 */       throw new IllegalArgumentException("channel index can not less than 0");
/*     */     }
/* 138 */     return (Viewer)new ViewerSample(ip, port, channelNo, event);
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public static void setSampleOption(Option option) {
/* 148 */     Option.instance = option;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public static Option getSampleOption() {
/* 158 */     return Option.instance;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public static void connectViewer(String ip, int port, int channelNo, ProtocolHandler handler) {
/* 174 */     Connector.instance().connect(ip, port, channelNo, handler);
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public static void connectVM(String ip, int port, int channelNo, ProtocolHandler handler, MediaType mediaType) {
/* 192 */     Connector.instance().connectVM(ip, port, channelNo, handler, mediaType);
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public static void loadFFmpegLib() {
/*     */     try {
/* 200 */       avutil.av_log_set_level(8);
/* 201 */       Loader.load(avutil.class);
/* 202 */       Loader.load(avcodec.class);
/* 203 */       Loader.load(avformat.class);
/* 204 */       Loader.load(swscale.class);
/* 205 */       avcodec.av_jni_set_java_vm(Loader.getJavaVM(), null);
/* 206 */     } catch (Throwable t) {
/* 207 */       log.error("FFmpeg static library initialization failure", t);
/*     */     } 
/*     */   }
/*     */ }


/* Location:              /Users/liu/Documents/工作文档/珑琪/智能盒子/kvm/svc-console-master/lib/svc-sdk-1.3.4.1/!/com/hiklife/svc/Kvm4JSdk.class
 * Java compiler version: 8 (52.0)
 * JD-Core Version:       1.1.3
 */