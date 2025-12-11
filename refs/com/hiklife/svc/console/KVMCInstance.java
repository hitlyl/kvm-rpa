/*     */ package com.hiklife.svc.console;
/*     */ import java.util.List;
/*     */ import java.util.concurrent.CompletableFuture;
/*     */ import org.apache.mina.core.future.WriteFuture;
/*     */ import org.apache.mina.core.session.IoSession;
/*     */ import org.bytedeco.ffmpeg.avutil.AVFrame;

import refs.com.hiklife.svc.Kvm4JSdk;
import refs.com.hiklife.svc.console.EnKeyMap;
import refs.com.hiklife.svc.console.KVMCAVFrameCallBack;
import refs.com.hiklife.svc.console.KVMCCloseCallBak;
import refs.com.hiklife.svc.console.KVMCInstance;
import refs.com.hiklife.svc.console.KVMCRealRawCallBack;
import refs.com.hiklife.svc.core.protocol.ProtocolHandler;
import refs.com.hiklife.svc.core.protocol.baseinfo.DevicePacket;
import refs.com.hiklife.svc.core.protocol.baseinfo.VersionPacket;
import refs.com.hiklife.svc.core.protocol.handler.ProtocolAuthEvent;
import refs.com.hiklife.svc.core.protocol.handler.ProtocolConnectEvent;
import refs.com.hiklife.svc.core.protocol.handler.ProtocolDeviceInfoEvent;
import refs.com.hiklife.svc.core.protocol.handler.ProtocolHandlerImpl;
import refs.com.hiklife.svc.core.protocol.handler.ProtocolViewerEvent;
import refs.com.hiklife.svc.core.protocol.normal.AudioParamPacket;
import refs.com.hiklife.svc.core.protocol.normal.BroadcastSetResultPacket;
import refs.com.hiklife.svc.core.protocol.normal.BroadcastStatusPacket;
import refs.com.hiklife.svc.core.protocol.normal.KeyEventPacket;
import refs.com.hiklife.svc.core.protocol.normal.KeyStatusPacket;
import refs.com.hiklife.svc.core.protocol.normal.MouseEventPacket;
import refs.com.hiklife.svc.core.protocol.normal.MouseTypePacket;
import refs.com.hiklife.svc.core.protocol.normal.VideoParamPacket;
import refs.com.hiklife.svc.core.protocol.normal.decoder.EncodingType;
import refs.com.hiklife.svc.core.protocol.security.SecurityType;
/*     */ 
/*     */ public class KVMCInstance {
/*     */   private String account;
/*     */   private String password;
/*     */   private KVMCAVFrameCallBack kvmCAVFrameCallBack;
/*     */   
/*     */   public CompletableFuture<Boolean> startSession(String ip, int port, int channelNo, String account, String password) {
/*  33 */     this.connectionFuture = new CompletableFuture<>();
/*  34 */     this.account = account;
/*  35 */     this.password = password;
/*  36 */     this.handler = (ProtocolHandler)new ProtocolHandlerImpl();
/*  37 */     ProtocolEvent protocolEvent = new ProtocolEvent();
/*     */     
/*  39 */     this.handler.addAuthEvent(protocolEvent);
/*     */     
/*  41 */     this.handler.addConnectEvent(protocolEvent);
/*     */     
/*  43 */     this.handler.addDeviceInfoEvent(protocolEvent);
/*     */     
/*  45 */     this.handler.addViewerEvent(protocolEvent);
/*  46 */     Kvm4JSdk.connectViewer(ip, port, channelNo, this.handler);
/*  47 */     return this.connectionFuture;
/*     */   }
/*     */   private KVMCCloseCallBak kvmcCloseCallBak; private KVMCRealRawCallBack kvmcRealRawCallBack; private ProtocolHandler handler; private CompletableFuture<Boolean> connectionFuture;
/*     */   
/*     */   public void stopSession() {
/*  52 */     this.handler.graceClose();
/*     */   }
/*     */   
/*     */   public ProtocolHandler getHandler() {
/*  56 */     return this.handler;
/*     */   }
/*     */   
/*     */   public void setKvmCCloseCallBak(KVMCCloseCallBak kvmcCloseCallBak) {
/*  60 */     this.kvmcCloseCallBak = kvmcCloseCallBak;
/*     */   }
/*     */   public void setKvmCAVFrameCallBack(KVMCAVFrameCallBack kvmCAVFrameCallBack) {
/*  63 */     this.kvmCAVFrameCallBack = kvmCAVFrameCallBack;
/*     */   }
/*     */   public void setKvmCRealRawCallBack(KVMCRealRawCallBack kvmcRealRawCallBack) {
/*  66 */     this.kvmcRealRawCallBack = kvmcRealRawCallBack;
/*     */   }
/*     */   
/*     */   public WriteFuture setABSMouseType() {
/*  70 */     return this.handler.writeCustomMouseType(new MouseTypePacket(1));
/*     */   }
/*     */   public WriteFuture setRELMouseModel() {
/*  73 */     return this.handler.writeCustomMouseType(new MouseTypePacket(0));
/*     */   }
/*     */   public WriteFuture sendKeyEvent(int down, int key) {
/*  76 */     return this.handler.writeKeyEvent(new KeyEventPacket(down, key));
/*     */   }
/*     */   public WriteFuture sendABSMouseEvent(int x, int y, int mask) {
/*  79 */     if (x < 0) x = 0; 
/*  80 */     if (y < 0) y = 0; 
/*  81 */     return this.handler.writeMouseEvent(new MouseEventPacket(x, y, mask, 1));
/*     */   }
/*     */   public WriteFuture sendRELMouseEvent(int x, int y, int mask) {
/*  84 */     return this.handler.writeMouseEvent(new MouseEventPacket(x, y, mask, 0));
/*     */   }
/*     */   
/*     */   public void autoSendEnChars(String chars) throws Exception {
/*  88 */     List<KeyEventPacket> list2Send = EnKeyMap.str2KeyEvent(chars);
/*  89 */     if (!list2Send.isEmpty()) {
/*  90 */       this.handler.writeKeyEvent(list2Send.<KeyEventPacket>toArray(new KeyEventPacket[0]));
/*     */     }
/*     */   }
/*     */   
/*     */   class ProtocolEvent
/*     */     implements ProtocolAuthEvent, ProtocolConnectEvent, ProtocolDeviceInfoEvent, ProtocolViewerEvent
/*     */   {
/*     */     public void onRequireAuth(SecurityType.Type type) {
/*  98 */       KVMCInstance.this.handler.callBackAuthInfo(type, KVMCInstance.this.account, KVMCInstance.this.password);
/*     */     }
/*     */ 
/*     */ 
/*     */     
/*     */     public void onAuthSuccess() {}
/*     */ 
/*     */ 
/*     */     
/*     */     public void onAuthFailed(String msg) {
/* 108 */       KVMCInstance.this.handler.graceClose();
/* 109 */       KVMCInstance.this.connectionFuture.complete(Boolean.valueOf(false));
/*     */     }
/*     */ 
/*     */ 
/*     */     
/*     */     public void onConnectSuccess(IoSession session) {}
/*     */ 
/*     */ 
/*     */     
/*     */     public void onConnectFailed() {
/* 119 */       onConnectClose("连接失败");
/*     */     }
/*     */ 
/*     */     
/*     */     public void onConnectClose(String closeInfo) {
/* 124 */       if (KVMCInstance.this.kvmcCloseCallBak != null) {
/* 125 */         KVMCInstance.this.kvmcCloseCallBak.invoke(closeInfo);
/*     */       }
/* 127 */       KVMCInstance.this.connectionFuture.complete(Boolean.valueOf(false));
/*     */     }
/*     */ 
/*     */ 
/*     */ 
/*     */     
/*     */     public void onInvalidRFBMessageException(Throwable cause) {}
/*     */ 
/*     */ 
/*     */     
/*     */     public void onCaughtException(Throwable cause) {}
/*     */ 
/*     */ 
/*     */     
/*     */     public void onAfterInitialisation() {
/* 142 */       KVMCInstance.this.connectionFuture.complete(Boolean.valueOf(true));
/*     */     }
/*     */ 
/*     */     
/*     */     public void onUpdateFrame(AVFrame frame) {
/* 147 */       if (KVMCInstance.this.kvmCAVFrameCallBack != null) {
/* 148 */         KVMCInstance.this.kvmCAVFrameCallBack.invoke(frame);
/*     */       }
/*     */     }
/*     */ 
/*     */     
/*     */     public void onUpdateVideoRawStream(byte[] bytes, EncodingType type) {
/* 154 */       if (KVMCInstance.this.kvmcRealRawCallBack != null)
/* 155 */         KVMCInstance.this.kvmcRealRawCallBack.invoke(bytes, type); 
/*     */     }
/*     */     
/*     */     public void onReadImageInfo(int width, int height) {}
/*     */     
/*     */     public void onChangeImageInfo(int width, int height) {}
/*     */     
/*     */     public void onUpdateAudio(byte[] bytes) {}
/*     */     
/*     */     public void onVideoParam(VideoParamPacket videoParamPacket) {}
/*     */     
/*     */     public void onAudioParam(AudioParamPacket audioParamPacket) {}
/*     */     
/*     */     public void onReadMouseType(MouseTypePacket mouseTypePacket) {}
/*     */     
/*     */     public void onKeyStatus(KeyStatusPacket keyStatusPacket) {}
/*     */     
/*     */     public void onBroadcastRequest(BroadcastStatusPacket broadcastStatusPacket) {}
/*     */     
/*     */     public void onBroadcastSet(BroadcastSetResultPacket broadcastSetResultPacket) {}
/*     */     
/*     */     public void onWriteCustomMouseType(MouseTypePacket mouseTypePacket) {}
/*     */     
/*     */     public void onGetDevice(DevicePacket device) {}
/*     */     
/*     */     public void onGetVersion(VersionPacket version) {}
/*     */   }
/*     */ }


/* Location:              /Users/liu/Documents/工作文档/珑琪/智能盒子/kvm/svc-console-master/lib/svc-sdk-1.3.4.1/!/com/hiklife/svc/console/KVMCInstance.class
 * Java compiler version: 8 (52.0)
 * JD-Core Version:       1.1.3
 */