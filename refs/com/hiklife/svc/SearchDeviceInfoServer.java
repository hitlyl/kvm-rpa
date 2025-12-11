/*     */ package com.hiklife.svc;
/*     */ import java.io.IOException;
/*     */ import java.net.DatagramPacket;
/*     */ import java.net.DatagramSocket;
/*     */ import java.net.InetAddress;
/*     */ import java.net.InetSocketAddress;
/*     */ import org.apache.mina.core.buffer.IoBuffer;
/*     */ import org.apache.mina.core.filterchain.DefaultIoFilterChainBuilder;
/*     */ import org.apache.mina.core.filterchain.IoFilter;
/*     */ import org.apache.mina.core.service.IoHandler;
/*     */ import org.apache.mina.core.session.IdleStatus;
/*     */ import org.apache.mina.core.session.IoSession;
/*     */ import org.apache.mina.filter.FilterEvent;
/*     */ import org.apache.mina.filter.codec.CumulativeProtocolDecoder;
/*     */ import org.apache.mina.filter.codec.ProtocolCodecFactory;
/*     */ import org.apache.mina.filter.codec.ProtocolCodecFilter;
/*     */ import org.apache.mina.filter.codec.ProtocolDecoder;
/*     */ import org.apache.mina.filter.codec.ProtocolDecoderOutput;
/*     */ import org.apache.mina.filter.codec.ProtocolEncoder;
/*     */ import org.apache.mina.filter.codec.ProtocolEncoderOutput;
/*     */ import org.apache.mina.transport.socket.DatagramSessionConfig;
/*     */ import org.apache.mina.transport.socket.nio.NioDatagramAcceptor;
/*     */ import org.slf4j.Logger;
/*     */ import org.slf4j.LoggerFactory;

import refs.com.hiklife.svc.SearchDeviceInfoServer;
import refs.com.hiklife.svc.SearchDeviceInfoServerListener;
import refs.com.hiklife.svc.util.HexUtils;
/*     */ 
/*     */ class SearchDeviceInfoServer
/*     */   implements IoHandler, ProtocolCodecFactory
/*     */ {
/*  31 */   private static final Logger log = LoggerFactory.getLogger(SearchDeviceInfoServer.class);
/*  32 */   private static final byte[] HIK_SEARCH_MESSAGE_BYTES = new byte[] { 104, 105, 107, 95, 115, 101, 97, 114, 99, 104, 95, 109, 101, 115, 115, 97, 103, 101, 0, 0 };
/*     */   
/*     */   private static final String HIK_SEARCH_MESSAGE = "hik_search_message";
/*     */   
/*     */   private static final String HIK_SEARCH_RESULT = "hik_search_result";
/*     */   
/*     */   private static final int HIK_SEARCH_FLAG_LENGTH = 20;
/*     */   
/*     */   private static final int HIK_SEARCH_RESULT_LENGTH = 56;
/*     */   
/*     */   private final NioDatagramAcceptor acceptor;
/*     */   
/*     */   private SearchDeviceInfoServerListener listener;
/*     */   
/*     */   private static class UdpServerHolder
/*     */   {
/*  48 */     private static final SearchDeviceInfoServer instance = new SearchDeviceInfoServer();
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public static SearchDeviceInfoServer instance() {
/*  56 */     return UdpServerHolder.instance;
/*     */   }
/*     */   
/*     */   private SearchDeviceInfoServer() {
/*  60 */     this.acceptor = new NioDatagramAcceptor();
/*  61 */     this.acceptor.setHandler(this);
/*  62 */     DefaultIoFilterChainBuilder chain = this.acceptor.getFilterChain();
/*  63 */     chain.addLast("codec", (IoFilter)new ProtocolCodecFilter(this));
/*  64 */     DatagramSessionConfig datagramSessionConfig = this.acceptor.getSessionConfig();
/*  65 */     datagramSessionConfig.setReuseAddress(true);
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   private void bind(int searchLocalServerUdpPort) throws IOException {
/*  74 */     this.acceptor.bind(new InetSocketAddress(searchLocalServerUdpPort));
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   private void unbind() {
/*  81 */     this.acceptor.unbind();
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void stop() {
/*  88 */     unbind();
/*  89 */     this.listener = null;
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
/*     */   public void search(int searchLocalServerUdpPort, int searchBroadcastPort, String ip, String subnetMask, SearchDeviceInfoServerListener listener) throws IOException {
/* 102 */     if (listener == null) {
/* 103 */       throw new IOException("SearchEvent Object is Null");
/*     */     }
/* 105 */     this.listener = listener;
/* 106 */     if (HexUtils.isEmpty(ip)) {
/* 107 */       listener.onSearchDeviceInfoError("ip地址不能为空");
/*     */       return;
/*     */     } 
/* 110 */     if (HexUtils.isEmpty(subnetMask)) {
/* 111 */       listener.onSearchDeviceInfoError("子网掩码不能为空");
/*     */       return;
/*     */     } 
/* 114 */     if (!this.acceptor.isActive()) {
/*     */       try {
/* 116 */         bind(searchLocalServerUdpPort);
/* 117 */       } catch (IOException e) {
/* 118 */         listener.onSearchDeviceInfoError("端口被占用");
/*     */       } 
/*     */     }
/* 121 */     (new Thread(() -> {
/*     */           try {
/*     */             broadCast(ip, subnetMask, searchBroadcastPort);
/* 124 */           } catch (IOException e) {
/*     */             listener.onSearchDeviceInfoError("发送失败");
/*     */           } 
/* 127 */         })).start();
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void sessionCreated(IoSession session) throws Exception {
/* 137 */     log.info("udp sessionCreated");
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void sessionOpened(IoSession session) throws Exception {
/* 147 */     log.info("udp sessionOpened");
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void sessionClosed(IoSession session) throws Exception {
/* 157 */     log.info("udp sessionClosed");
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void sessionIdle(IoSession session, IdleStatus status) throws Exception {
/* 168 */     log.info("udp sessionIdle");
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void exceptionCaught(IoSession session, Throwable cause) throws Exception {
/* 179 */     log.info("udp exceptionCaught", cause);
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void messageReceived(IoSession session, Object message) throws Exception {
/* 190 */     log.info("udp messageReceived");
/* 191 */     String clientIp = ((InetSocketAddress)session.getRemoteAddress()).getAddress().getHostAddress();
/* 192 */     handleMessage((byte[])message, clientIp);
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void messageSent(IoSession session, Object message) throws Exception {
/* 203 */     log.info("udp messageSent");
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void inputClosed(IoSession session) throws Exception {
/* 213 */     log.info("udp inputClosed");
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
/*     */   public void event(IoSession session, FilterEvent event) throws Exception {}
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public ProtocolEncoder getEncoder(IoSession session) throws Exception {
/* 236 */     return new ProtocolEncoder()
/*     */       {
/*     */         public void encode(IoSession session, Object message, ProtocolEncoderOutput out) {}
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */         
/*     */         public void dispose(IoSession session) {}
/*     */       };
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public ProtocolDecoder getDecoder(IoSession session) throws Exception {
/* 257 */     return (ProtocolDecoder)new CumulativeProtocolDecoder()
/*     */       {
/*     */         protected boolean doDecode(IoSession session, IoBuffer buffer, ProtocolDecoderOutput out) throws Exception
/*     */         {
/* 261 */           int remainingLength = buffer.remaining();
/* 262 */           if (remainingLength < 20) {
/* 263 */             buffer.position(buffer.limit());
/* 264 */             return false;
/*     */           } 
/* 266 */           buffer.mark();
/* 267 */           byte[] temp = new byte[remainingLength];
/* 268 */           buffer.get(temp);
/* 269 */           buffer.position(buffer.position());
/* 270 */           int length = SearchDeviceInfoServer.this.segmentMessage(temp);
/* 271 */           buffer.reset();
/*     */           
/* 273 */           if (length > 0) {
/* 274 */             byte[] bytes = new byte[length];
/* 275 */             buffer.get(bytes, 0, length);
/* 276 */             out.write(bytes);
/* 277 */             return true;
/*     */           } 
/* 279 */           return false;
/*     */         }
/*     */       };
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   private int segmentMessage(byte[] temp) {
/* 291 */     String msg = HexUtils.bytesToAscii(temp, 20);
/* 292 */     if (msg.startsWith("hik_search_result")) {
/* 293 */       if (temp.length >= 56) {
/* 294 */         return 56;
/*     */       }
/* 296 */       return 0;
/*     */     } 
/* 298 */     if (msg.startsWith("hik_search_message")) {
/* 299 */       return 20;
/*     */     }
/* 301 */     return temp.length;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   private void handleMessage(byte[] message, String ip) {
/* 311 */     log.debug("message.length: {}", Integer.valueOf(message.length));
/* 312 */     int length = message.length;
/* 313 */     if (length == 56) {
/* 314 */       Device4Search device4Search = new Device4Search(message, ip);
/* 315 */       if (this.listener != null) {
/* 316 */         this.listener.onSearchDeviceInfo(device4Search.ip, device4Search.port, device4Search.type);
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
/*     */   private void broadCast(String ip, String subnetMask, int searchBroadcastPort) throws IOException {
/* 329 */     InetAddress ipAddress = InetAddress.getByName(ip);
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
/* 344 */     DatagramSocket ds = new DatagramSocket();
/* 345 */     DatagramPacket dp = new DatagramPacket(HIK_SEARCH_MESSAGE_BYTES, 20, ipAddress, searchBroadcastPort);
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */     
/* 351 */     ds.send(dp);
/* 352 */     ds.close();
/*     */   }
/*     */ 
/*     */ 
/*     */   
/*     */   static class Device4Search
/*     */   {
/*     */     private int type;
/*     */ 
/*     */     
/*     */     private int port;
/*     */ 
/*     */     
/*     */     private String ip;
/*     */ 
/*     */ 
/*     */     
/*     */     public Device4Search(byte[] msg, String ip) {
/* 370 */       this.type = HexUtils.bytesToIntLittle(msg, 20);
/* 371 */       this.port = HexUtils.bytesToIntLittle(msg, 52);
/* 372 */       this.ip = ip;
/*     */     }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */     
/*     */     public int getType() {
/* 380 */       return this.type;
/*     */     }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */     
/*     */     public void setType(int type) {
/* 388 */       this.type = type;
/*     */     }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */     
/*     */     public int getPort() {
/* 396 */       return this.port;
/*     */     }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */     
/*     */     public void setPort(int port) {
/* 404 */       this.port = port;
/*     */     }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */     
/*     */     public String getIp() {
/* 412 */       return this.ip;
/*     */     }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */     
/*     */     public void setIp(String ip) {
/* 420 */       this.ip = ip;
/*     */     }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */     
/*     */     public String toString() {
/* 429 */       return "SearchDevice{type=" + this.type + ", port=" + this.port + ", ip=" + this.ip + '}';
/*     */     }
/*     */   }
/*     */ }


/* Location:              /Users/liu/Documents/工作文档/珑琪/智能盒子/kvm/svc-console-master/lib/svc-sdk-1.3.4.1/!/com/hiklife/svc/SearchDeviceInfoServer.class
 * Java compiler version: 8 (52.0)
 * JD-Core Version:       1.1.3
 */