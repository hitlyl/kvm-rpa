/*     */ package com.hiklife.svc.core.net;
/*     */ import java.net.InetSocketAddress;
/*     */ import org.apache.mina.core.filterchain.IoFilter;
/*     */ import org.apache.mina.core.future.ConnectFuture;
/*     */ import org.apache.mina.core.service.IoHandler;
/*     */ import org.apache.mina.core.session.IdleStatus;
/*     */ import org.apache.mina.core.session.IoSession;
/*     */ import org.apache.mina.filter.FilterEvent;
/*     */ import org.apache.mina.filter.codec.ProtocolCodecFilter;
/*     */ import org.apache.mina.transport.socket.SocketSessionConfig;
/*     */ import org.apache.mina.transport.socket.nio.NioSocketConnector;
/*     */ import org.slf4j.Logger;
/*     */ import org.slf4j.LoggerFactory;

import refs.com.hiklife.svc.core.net.Connector;
import refs.com.hiklife.svc.core.net.ProtocolCodec;
import refs.com.hiklife.svc.core.protocol.InvalidRFBMessageException;
import refs.com.hiklife.svc.core.protocol.ProtocolHandler;
import refs.com.hiklife.svc.core.protocol.handler.ProtocolConnectEvent;
import refs.com.hiklife.svc.core.protocol.handler.ProtocolVMEvent;
import refs.com.hiklife.svc.core.protocol.normal.decoder.EncodingType;
import refs.com.hiklife.svc.core.protocol.vm.MediaType;
import refs.com.hiklife.svc.util.HexUtils;
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ public class Connector
/*     */   implements IoHandler
/*     */ {
/*  33 */   private static final Logger log = LoggerFactory.getLogger(Connector.class);
/*     */   
/*     */   public static final int CONNECT_TIMEOUT_SECONDS = 3;
/*     */   
/*     */   public static final int CONNECT_WRITER_IDLE_SECONDS = 3;
/*     */   public static final int CONNECT_READER_IDLE_SECONDS = 3;
/*     */   private final NioSocketConnector socket;
/*     */   private boolean isConnected = false;
/*     */   
/*     */   private Connector() {
/*  43 */     this.socket = new NioSocketConnector();
/*  44 */     this.socket.getFilterChain().addFirst("codec", (IoFilter)new ProtocolCodecFilter(new ProtocolCodec()));
/*  45 */     this.socket.setHandler(this);
/*  46 */     this.socket.setConnectTimeoutMillis(3000L);
/*  47 */     this.socket.getSessionConfig().setWriterIdleTime(3);
/*  48 */     this.socket.getSessionConfig().setReaderIdleTime(3);
/*     */   }
/*     */   
/*     */   private static class ConnectorHolder {
/*  52 */     private static final Connector instance = new Connector(); }
/*     */   
/*     */   public static Connector instance() {
/*  55 */     return ConnectorHolder.instance;
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
/*     */   public void connect(String ip, int port, int channelNo, ProtocolHandler handler) {
/*  67 */     log.info("Start connect:{} {}", ip, Integer.valueOf(port));
/*  68 */     ProtocolConnectEvent event = handler.getConnectEvent();
/*  69 */     ConnectFuture future = this.socket.connect(new InetSocketAddress(ip, port), (ioSession, ioFuture) -> {
/*     */           ioSession.setAttribute("handler", handler);
/*     */           
/*     */           handler.getContext().setIp(ip);
/*     */           handler.getContext().setPort(port);
/*     */           handler.getContext().setChannelNo(channelNo);
/*     */           handler.getContext().setStartTime(System.currentTimeMillis());
/*     */           handler.getContext().setEncodingType(EncodingType.H264);
/*     */           handler.getContext().setTrueColor(true);
/*     */           if (event != null) {
/*     */             event.onConnectSuccess(ioFuture.getSession());
/*     */           }
/*     */           this.isConnected = true;
/*     */           log.info("Success connect:{} {}", ip, Integer.valueOf(port));
/*     */         });
/*  84 */     future.awaitUninterruptibly();
/*  85 */     if (event != null && !this.isConnected) {
/*  86 */       event.onConnectFailed();
/*  87 */       log.info("Failed connect:{} {}", ip, Integer.valueOf(port));
/*     */     } 
/*  89 */     this.isConnected = false;
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
/*     */   public void connectVM(String ip, int port, int channelNo, ProtocolHandler handler, MediaType mediaType) {
/* 103 */     handler.getContext().setMediaType(mediaType);
/* 104 */     handler.getContext().setHandlerType(1);
/* 105 */     connect(ip, port, channelNo, handler);
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void sessionCreated(IoSession session) {
/* 115 */     SocketSessionConfig cfg = (SocketSessionConfig)session.getConfig();
/* 116 */     cfg.setSoLinger(0);
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void sessionOpened(IoSession session) {
/* 126 */     ProtocolHandler handler = (ProtocolHandler)session.getAttribute("handler");
/* 127 */     handler.setSession(session);
/* 128 */     handler.onConnectSuccess();
/* 129 */     log.debug("sessionOpened,ioSession:{}", session);
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void sessionClosed(IoSession session) {
/* 139 */     log.debug("sessionClosed,ioSession:{}", session);
/* 140 */     ProtocolHandler handler = (ProtocolHandler)session.getAttribute("handler");
/* 141 */     ProtocolConnectEvent event = handler.getConnectEvent();
/* 142 */     String closeInfo = (String)session.getAttribute("closeInfo");
/* 143 */     handler.destroy();
/* 144 */     if (event != null) {
/* 145 */       event.onConnectClose(closeInfo);
/*     */     }
/* 147 */     System.gc();
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void sessionIdle(IoSession session, IdleStatus status) {
/* 158 */     ProtocolHandler handler = (ProtocolHandler)session.getAttribute("handler");
/* 159 */     ProtocolVMEvent vmEvent = handler.getVMEvent();
/*     */     
/* 161 */     if (status == IdleStatus.READER_IDLE) {
/* 162 */       if (handler.getContext().getHandlerType() == 1)
/*     */       {
/* 164 */         if (vmEvent != null) {
/* 165 */           vmEvent.onVMReadEnd();
/*     */         }
/*     */       }
/* 168 */     } else if (status == IdleStatus.WRITER_IDLE) {
/* 169 */       handler.writeKeepAlive();
/* 170 */       if (handler.getContext().getHandlerType() == 1)
/*     */       {
/* 172 */         if (vmEvent != null) {
/* 173 */           vmEvent.onVMWriteEnd();
/*     */         }
/*     */       }
/*     */     } 
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void exceptionCaught(IoSession session, Throwable cause) {
/* 187 */     log.error("exceptionCaught,ioSession:{}", session, cause);
/* 188 */     ProtocolHandler handler = (ProtocolHandler)session.getAttribute("handler");
/* 189 */     ProtocolConnectEvent event = handler.getConnectEvent();
/* 190 */     if (cause instanceof java.io.IOException) {
/* 191 */       log.info("客户端[" + session.getRemoteAddress() + "]异常断开");
/* 192 */       if (event != null) {
/* 193 */         event.onCaughtException(cause);
/*     */       }
/* 195 */       handler.graceClose();
/*     */     } else {
/* 197 */       if (event != null) {
/* 198 */         event.onCaughtException(cause);
/*     */       }
/* 200 */       if (handler.getContext().getHandlerType() == 1) {
/* 201 */         handler.graceClose();
/*     */       }
/*     */     } 
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void messageReceived(IoSession session, Object message) {
/* 214 */     log.trace("messageReceived,ioSession:{},Object:{}", Long.valueOf(session.getId()), HexUtils.bytesToHexString((byte[])message));
/* 215 */     ProtocolHandler handler = (ProtocolHandler)session.getAttribute("handler");
/* 216 */     ProtocolConnectEvent event = handler.getConnectEvent();
/* 217 */     handler.getContext().setFlow(handler.getContext().getFlow() + ((byte[])message).length);
/*     */     try {
/* 219 */       handler.handleProtocolMessage((byte[])message);
/* 220 */     } catch (InvalidRFBMessageException e) {
/* 221 */       log.error("InvalidRFBMessageException:{}", e.getMessage());
/* 222 */       if (event != null) {
/* 223 */         event.onInvalidRFBMessageException(e.getCause());
/*     */       }
/* 225 */       handler.graceClose();
/*     */     } 
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void messageSent(IoSession session, Object message) {
/* 237 */     log.trace("messageSent,ioSession:{},Object:{}", Long.valueOf(session.getId()), HexUtils.bytesToHexString((byte[])message));
/* 238 */     ProtocolHandler handler = (ProtocolHandler)session.getAttribute("handler");
/* 239 */     handler.getContext().setFlow(handler.getContext().getFlow() + ((byte[])message).length);
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void inputClosed(IoSession session) {
/* 249 */     log.info("inputClosed");
/* 250 */     ProtocolHandler handler = (ProtocolHandler)session.getAttribute("handler");
/* 251 */     handler.graceClose();
/*     */   }
/*     */   
/*     */   public void event(IoSession session, FilterEvent event) throws Exception {}
/*     */ }


/* Location:              /Users/liu/Documents/工作文档/珑琪/智能盒子/kvm/svc-console-master/lib/svc-sdk-1.3.4.1/!/com/hiklife/svc/core/net/Connector.class
 * Java compiler version: 8 (52.0)
 * JD-Core Version:       1.1.3
 */