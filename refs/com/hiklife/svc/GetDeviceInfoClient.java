/*    */ package com.hiklife.svc;
/*    */ import org.apache.mina.core.session.IoSession;

import refs.com.hiklife.svc.GetDeviceInfoClientListener;
import refs.com.hiklife.svc.core.net.Connector;
import refs.com.hiklife.svc.core.protocol.ProtocolHandler;
import refs.com.hiklife.svc.core.protocol.baseinfo.DevicePacket;
import refs.com.hiklife.svc.core.protocol.baseinfo.VersionPacket;
import refs.com.hiklife.svc.core.protocol.handler.ProtocolConnectEvent;
import refs.com.hiklife.svc.core.protocol.handler.ProtocolDeviceInfoEvent;
import refs.com.hiklife.svc.core.protocol.handler.ProtocolHandlerImpl;
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ class GetDeviceInfoClient
/*    */   implements ProtocolDeviceInfoEvent, ProtocolConnectEvent
/*    */ {
/*    */   private ProtocolHandler protocolHandler;
/*    */   private GetDeviceInfoClientListener event;
/*    */   
/*    */   public void start(String ip, int port, GetDeviceInfoClientListener event) {
/* 33 */     this.protocolHandler = (ProtocolHandler)new ProtocolHandlerImpl();
/* 34 */     this.protocolHandler.addConnectEvent(this);
/* 35 */     this.protocolHandler.addDeviceInfoEvent(this);
/* 36 */     this.event = event;
/* 37 */     Connector.instance().connect(ip, port, 0, this.protocolHandler);
/*    */   }
/*    */   
/*    */   private void destroy() {
/* 41 */     if (this.protocolHandler.getSession() != null) {
/* 42 */       this.protocolHandler.getSession().closeOnFlush();
/* 43 */       this.protocolHandler.destroy();
/*    */     } 
/*    */   }
/*    */ 
/*    */ 
/*    */   
/*    */   public void onConnectSuccess(IoSession session) {}
/*    */ 
/*    */ 
/*    */   
/*    */   public void onConnectFailed() {
/* 54 */     this.event.onGetDeviceInfoError("Device not detected at the specified IP");
/* 55 */     destroy();
/*    */   }
/*    */ 
/*    */ 
/*    */   
/*    */   public void onConnectClose(String closeInfo) {}
/*    */ 
/*    */ 
/*    */   
/*    */   public void onGetDevice(DevicePacket device) {
/* 65 */     this.event.onGetDeviceInfo(device);
/* 66 */     destroy();
/*    */   }
/*    */ 
/*    */ 
/*    */   
/*    */   public void onGetVersion(VersionPacket version) {}
/*    */ 
/*    */ 
/*    */   
/*    */   public void onInvalidRFBMessageException(Throwable cause) {
/* 76 */     this.event.onGetDeviceInfoError("Internal protocol error");
/*    */   }
/*    */ 
/*    */ 
/*    */   
/*    */   public void onCaughtException(Throwable cause) {
/* 82 */     this.event.onGetDeviceInfoError(cause.toString());
/*    */   }
/*    */   
/*    */   public void onAfterInitialisation() {}
/*    */ }


/* Location:              /Users/liu/Documents/工作文档/珑琪/智能盒子/kvm/svc-console-master/lib/svc-sdk-1.3.4.1/!/com/hiklife/svc/GetDeviceInfoClient.class
 * Java compiler version: 8 (52.0)
 * JD-Core Version:       1.1.3
 */