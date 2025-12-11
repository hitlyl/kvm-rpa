/*      */ package com.hiklife.svc.core.protocol.handler;
/*      */ import java.util.concurrent.atomic.AtomicBoolean;
/*      */ import org.apache.mina.core.future.WriteFuture;
/*      */ import org.apache.mina.core.session.IoSession;
/*      */ import org.bytedeco.ffmpeg.avutil.AVFrame;

import com.hiklife.svc.core.protocol.ProtocolHandler;
import com.hiklife.svc.core.protocol.normal.decoder.FFmpegDecoder;
import com.hiklife.svc.core.protocol.normal.decoder.G726Decoder;

import refs.com.hiklife.svc.core.protocol.InvalidRFBMessageException;
import refs.com.hiklife.svc.core.protocol.ProtocolContext;
import refs.com.hiklife.svc.core.protocol.baseinfo.DevicePacket;
import refs.com.hiklife.svc.core.protocol.baseinfo.VersionPacket;
import refs.com.hiklife.svc.core.protocol.handler.ProtocolAuthEvent;
import refs.com.hiklife.svc.core.protocol.handler.ProtocolConnectEvent;
import refs.com.hiklife.svc.core.protocol.handler.ProtocolDeviceInfoEvent;
import refs.com.hiklife.svc.core.protocol.handler.ProtocolHandlerImpl;
import refs.com.hiklife.svc.core.protocol.handler.ProtocolVMEvent;
import refs.com.hiklife.svc.core.protocol.handler.ProtocolViewerEvent;
import refs.com.hiklife.svc.core.protocol.initialisation.ImageInfo;
import refs.com.hiklife.svc.core.protocol.initialisation.InitialisationPacket;
import refs.com.hiklife.svc.core.protocol.normal.AudioFramePacket;
import refs.com.hiklife.svc.core.protocol.normal.AudioParamPacket;
import refs.com.hiklife.svc.core.protocol.normal.BroadcastSetResultPacket;
import refs.com.hiklife.svc.core.protocol.normal.BroadcastStatusPacket;
import refs.com.hiklife.svc.core.protocol.normal.KeyEventPacket;
import refs.com.hiklife.svc.core.protocol.normal.KeyStatusPacket;
import refs.com.hiklife.svc.core.protocol.normal.MouseEventPacket;
import refs.com.hiklife.svc.core.protocol.normal.MouseTypePacket;
import refs.com.hiklife.svc.core.protocol.normal.ReadNormalType;
import refs.com.hiklife.svc.core.protocol.normal.VideoFramePacket;
import refs.com.hiklife.svc.core.protocol.normal.VideoParamPacket;
import refs.com.hiklife.svc.core.protocol.normal.decoder.EncodingType;
import refs.com.hiklife.svc.core.protocol.security.AuthResult;
import refs.com.hiklife.svc.core.protocol.security.RsaAuth;
import refs.com.hiklife.svc.core.protocol.security.SecurityInput;
import refs.com.hiklife.svc.core.protocol.security.SecurityType;
import refs.com.hiklife.svc.core.protocol.security.VncAuthPacket;
import refs.com.hiklife.svc.core.protocol.vm.VMLinkPacket;
import refs.com.hiklife.svc.core.protocol.vm.VMReadPacket;
import refs.com.hiklife.svc.core.protocol.vm.VMWritePacket;
import refs.com.hiklife.svc.util.HexUtils;
/*      */ 
/*      */ public class ProtocolHandlerImpl implements ProtocolHandler {
/*   35 */   private static final Logger log = LoggerFactory.getLogger(ProtocolHandlerImpl.class);
/*      */   private static final int EMPTY_VIDEO_LENGTH = 4;
/*   37 */   private static final byte[] KEEP_ALIVE_BYTES = new byte[] { 101, 0, 0, 0 };
/*   38 */   private static final byte[] SHARE_BYTE = new byte[] { 1 };
/*   39 */   private static final byte[] VIDEO_PARAM_REQUEST = new byte[] { 102, 0, 0, 0 };
/*   40 */   private static final byte[] AUDIO_PARAM_REQUEST = new byte[] { 107, 0, 0, 0 };
/*   41 */   private static final byte[] MOUSE_TYPE_REQUEST = new byte[] { 109, 0, 0, 0 };
/*   42 */   private static final byte[] KEY_TYPE_REQUEST = new byte[] { 104, 0, 0, 0 };
/*   43 */   private static final byte[] BROADCAST_REQUEST = new byte[] { -55, 0, 0, 0 };
/*   44 */   private static final byte[] VM_CLOSE_REQUEST = new byte[] { 11, 0, 0, 0 };
/*   45 */   private final AtomicBoolean hasRun = new AtomicBoolean(false);
/*      */   
/*      */   private IoSession session;
/*   48 */   private ProtocolStage state = ProtocolStage.PROTOCOL_VERSION;
/*      */   private SecurityInput securityInput;
/*   50 */   private final VideoFramePacket videoFramePacket = new VideoFramePacket((FFmpegDecoder.Event)this);
/*   51 */   private final AudioFramePacket audioFramePacket = new AudioFramePacket((G726Decoder.Event)this);
/*   52 */   private final ProtocolContext protocolContext = new ProtocolContext();
/*      */   
/*      */   private DevicePacket device;
/*      */   
/*      */   private ProtocolVMEvent vmEvent;
/*      */   
/*      */   private ProtocolAuthEvent authEvent;
/*      */   private ProtocolViewerEvent viewerEvent;
/*      */   private ProtocolConnectEvent connectEvent;
/*      */   private ProtocolDeviceInfoEvent deviceInfoEvent;
/*      */   
/*      */   public void onConnectSuccess() {
/*      */     try {
/*   65 */       writeProtocolVersion(VersionPacket.VERSION_3_8.formatVersion());
/*   66 */     } catch (InvalidRFBMessageException e) {
/*   67 */       log.error("Send Version Message Error", e.getCause());
/*      */     } 
/*      */   }
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */   
/*      */   public void addConnectEvent(ProtocolConnectEvent connectEvent) {
/*   77 */     this.connectEvent = connectEvent;
/*      */   }
/*      */   
/*      */   public boolean isSecurityTypesMessage() {
/*   81 */     return (this.state == ProtocolStage.SECURITY_TYPES);
/*      */   }
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */   
/*      */   public ProtocolConnectEvent getConnectEvent() {
/*   89 */     return this.connectEvent;
/*      */   }
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */   
/*      */   public void addDeviceInfoEvent(ProtocolDeviceInfoEvent deviceInfoEvent) {
/*   99 */     this.deviceInfoEvent = deviceInfoEvent;
/*      */   }
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */   
/*      */   public void addViewerEvent(ProtocolViewerEvent viewerEvent) {
/*  109 */     this.viewerEvent = viewerEvent;
/*      */   }
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */   
/*      */   public void addVMEvent(ProtocolVMEvent vmEvent) {
/*  119 */     this.vmEvent = vmEvent;
/*      */   }
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */   
/*      */   public ProtocolVMEvent getVMEvent() {
/*  128 */     return this.vmEvent;
/*      */   }
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */   
/*      */   public void addAuthEvent(ProtocolAuthEvent authEvent) {
/*  138 */     this.authEvent = authEvent;
/*      */   }
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */   
/*      */   public IoSession getSession() {
/*  148 */     return this.session;
/*      */   }
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */   
/*      */   public boolean isBeforeNormal() {
/*  158 */     return (this.state != ProtocolStage.NORMAL);
/*      */   }
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */   
/*      */   public void setSession(IoSession session) {
/*  168 */     this.session = session;
/*      */   }
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */   
/*      */   public void destroy() {
/*  176 */     if (this.hasRun.compareAndSet(false, true)) {
/*  177 */       if (this.videoFramePacket.fFmpegVideoDecoder != null) {
/*  178 */         this.videoFramePacket.fFmpegVideoDecoder.destroy();
/*      */       }
/*  180 */       if (this.audioFramePacket.decoder != null) {
/*  181 */         this.audioFramePacket.decoder.destroy();
/*      */       }
/*  183 */       if (this.protocolContext.getHandlerType() == 1) {
/*  184 */         DiskMemory.closeHandle("");
/*  185 */         if (this.session != null) {
/*  186 */           writeVMCloseRequest();
/*      */         }
/*      */       } 
/*  189 */       log.debug("Protocol Handler Destroy!");
/*      */     } 
/*      */   }
/*      */ 
/*      */   
/*      */   public void callBackAuthInfo(SecurityType.Type type, String account, String password) {
/*  195 */     this.securityInput = new SecurityInput();
/*  196 */     this.securityInput.setPassword(password);
/*  197 */     this.securityInput.setAccount(account);
/*  198 */     this.protocolContext.setSecurityType(type);
/*  199 */     byte[] path = { (byte)this.protocolContext.getChannelNo() };
/*  200 */     writeSecurityType(new byte[] { type.getCode() });
/*  201 */     byte[] msg = new byte[1 + path.length];
/*  202 */     msg[0] = (byte)path.length;
/*  203 */     System.arraycopy(path, 0, msg, 1, path.length);
/*      */     
/*  205 */     if (type == SecurityType.Type.CENTRALIZE_AUTH) {
/*  206 */       String userAccount = this.securityInput.getAccount();
/*  207 */       byte[] accountStr = userAccount.getBytes(StandardCharsets.US_ASCII);
/*  208 */       byte[] userMsg = new byte[17];
/*  209 */       userMsg[0] = 16;
/*  210 */       System.arraycopy(accountStr, 0, userMsg, 1, accountStr.length);
/*  211 */       writeUserAccount(userMsg);
/*  212 */       writeSecurityPath(msg);
/*  213 */       this.state = ProtocolStage.CENTRALIZE_TYPES;
/*  214 */     } else if (type == SecurityType.Type.NONE) {
/*  215 */       writeSecurityPath(msg);
/*  216 */       this.state = ProtocolStage.SECURITY_RESULT;
/*      */     } else {
/*  218 */       writeSecurityPath(msg);
/*  219 */       this.state = ProtocolStage.SECURITY;
/*      */     } 
/*      */   }
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */   
/*      */   public boolean isNormalMessage() {
/*  230 */     return (this.state == ProtocolStage.NORMAL);
/*      */   }
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */   
/*      */   public boolean isCentralizeMessage() {
/*  240 */     return (this.state == ProtocolStage.CENTRALIZE_TYPES);
/*      */   }
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */   
/*      */   public boolean isVersionMessage() {
/*  250 */     return (this.state == ProtocolStage.PROTOCOL_VERSION);
/*      */   }
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */   
/*      */   public void handleProtocolMessage(byte[] bytes) throws InvalidRFBMessageException {
/*  261 */     log.trace("Handle protocol Message, 0x{}", HexUtils.bytesToHexString(bytes));
/*  262 */     switch (this.state) {
/*      */       case FrameBufferUpdate:
/*      */       case SetColourMapEntries:
/*  265 */         readProtocolVersion(bytes);
/*      */         break;
/*      */       case Bell:
/*  268 */         readSecurityTypes(bytes);
/*      */         break;
/*      */       case ServerCutText:
/*  271 */         readSecurityTypesCtz(bytes);
/*      */         break;
/*      */       case AudioBufferUpdate:
/*  274 */         readSecurity(bytes);
/*      */         break;
/*      */       case VMRead:
/*  277 */         readSecurityResult(bytes);
/*      */         break;
/*      */       case VMWrite:
/*  280 */         readInitialisation(bytes);
/*      */         break;
/*      */       case VideoParam:
/*  283 */         readNormal(bytes);
/*      */         break;
/*      */       case KeyStatus:
/*  286 */         log.error("Handle Error Protocol Message, {}", HexUtils.bytesToHexString(bytes));
/*      */         break;
/*      */     } 
/*      */   }
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */   
/*      */   public void onDecodeFrame(AVFrame avFrame) {
/*  298 */     if (this.viewerEvent != null) {
/*  299 */       this.viewerEvent.onUpdateFrame(avFrame);
/*      */     }
/*      */   }
/*      */ 
/*      */   
/*      */   public void onDecodeVideoRawStream(byte[] bytes, EncodingType type) {
/*  305 */     if (this.viewerEvent != null) {
/*  306 */       this.viewerEvent.onUpdateVideoRawStream(bytes, type);
/*      */     }
/*      */   }
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */   
/*      */   public void onAudioDecodeFrame(byte[] audioBytes) {
/*  317 */     if (this.viewerEvent != null) {
/*  318 */       this.viewerEvent.onUpdateAudio(audioBytes);
/*      */     }
/*      */   }
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */   
/*      */   public void readProtocolVersion(byte[] orgMsgBytes) throws InvalidRFBMessageException {
/*  329 */     VersionPacket version = new VersionPacket(orgMsgBytes);
/*  330 */     log.debug("readProtocolVersion: {}-{}", Integer.valueOf(version.getMajor()), Integer.valueOf(version.getMinor()));
/*  331 */     this.device = new DevicePacket(orgMsgBytes);
/*  332 */     this.protocolContext.setDevice(this.device);
/*      */     
/*  334 */     this.state = ProtocolStage.SECURITY_TYPES;
/*  335 */     if (this.deviceInfoEvent != null) {
/*  336 */       this.deviceInfoEvent.onGetDevice(this.device);
/*  337 */       this.deviceInfoEvent.onGetVersion(version);
/*      */     } 
/*      */ 
/*      */     
/*  341 */     if (this.authEvent != null) {
/*  342 */       int deviceBytesLength = DevicePacket.length(orgMsgBytes);
/*  343 */       if (orgMsgBytes.length > deviceBytesLength) {
/*  344 */         int bytesLength = orgMsgBytes.length - deviceBytesLength;
/*  345 */         byte[] bytes = new byte[bytesLength];
/*  346 */         System.arraycopy(orgMsgBytes, deviceBytesLength, bytes, 0, bytesLength);
/*  347 */         handleProtocolMessage(bytes);
/*      */       } 
/*      */     } 
/*      */   }
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */   
/*      */   public void readSecurityTypesCtz(byte[] orgMsgBytes) throws InvalidRFBMessageException {
/*  360 */     log.debug("readSecurityTypesCtz: {}", HexUtils.bytesToHexString(orgMsgBytes));
/*  361 */     byte[] orgMsg = new byte[2];
/*  362 */     orgMsg[0] = 1;
/*  363 */     orgMsg[1] = orgMsgBytes[0];
/*  364 */     SecurityType securityType = new SecurityType(orgMsg);
/*  365 */     if (securityType.getTypes().isEmpty()) {
/*  366 */       log.error("No authentication methods provided");
/*      */     }
/*  368 */     else if (securityType.getTypes().contains(SecurityType.Type.NONE)) {
/*  369 */       this.state = ProtocolStage.SECURITY_RESULT;
/*  370 */     } else if (securityType.getTypes().contains(SecurityType.Type.VNC_AUTH)) {
/*  371 */       this.protocolContext.setSecurityType(SecurityType.Type.VNC_AUTH);
/*  372 */       this.state = ProtocolStage.SECURITY;
/*      */     } else {
/*  374 */       log.error("Authentication method not supported");
/*      */     } 
/*      */   }
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */   
/*      */   public void readSecurityTypes(byte[] orgMsgBytes) throws InvalidRFBMessageException {
/*  386 */     log.debug("readSecurityTypes: {}", HexUtils.bytesToHexString(orgMsgBytes));
/*  387 */     SecurityType securityType = new SecurityType(orgMsgBytes);
/*  388 */     if (securityType.getTypes().isEmpty()) {
/*  389 */       log.error("No authentication methods provided");
/*      */     }
/*  391 */     if (securityType.getTypes().contains(SecurityType.Type.NONE)) {
/*  392 */       callBackAuthInfo(SecurityType.Type.NONE, "", "");
/*      */     }
/*  394 */     else if (this.authEvent != null) {
/*  395 */       if (securityType.getTypes().contains(SecurityType.Type.VNC_AUTH)) {
/*  396 */         this.authEvent.onRequireAuth(SecurityType.Type.VNC_AUTH);
/*  397 */       } else if (securityType.getTypes().contains(SecurityType.Type.CENTRALIZE_AUTH)) {
/*  398 */         this.authEvent.onRequireAuth(SecurityType.Type.CENTRALIZE_AUTH);
/*      */       } else {
/*  400 */         log.error("Authentication method not supported");
/*      */       } 
/*      */     } else {
/*      */       
/*  404 */       throw new InvalidRFBMessageException("No authentication callback event was implemented");
/*      */     } 
/*      */   }
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */   
/*      */   public void readSecurity(byte[] orgMsgBytes) throws InvalidRFBMessageException {
/*      */     VncAuthPacket vncAuthPacket;
/*      */     RsaAuth rsaAuth;
/*  419 */     log.debug("readSecurity: {}", HexUtils.bytesToHexString(orgMsgBytes));
/*  420 */     switch (this.protocolContext.getSecurityType()) {
/*      */       case FrameBufferUpdate:
/*  422 */         vncAuthPacket = new VncAuthPacket(orgMsgBytes, this.securityInput);
/*  423 */         writeVncAuth(vncAuthPacket.encrypt());
/*      */         break;
/*      */       case SetColourMapEntries:
/*  426 */         rsaAuth = new RsaAuth(orgMsgBytes, this.securityInput);
/*  427 */         writeRsaAuth(rsaAuth.encrypt());
/*      */         break;
/*      */     } 
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */     
/*  436 */     this.state = ProtocolStage.SECURITY_RESULT;
/*      */   }
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */   
/*      */   public void readSecurityResult(byte[] orgMsgBytes) {
/*  445 */     log.debug("readSecurityResult: {}", HexUtils.bytesToHexString(orgMsgBytes));
/*  446 */     AuthResult authResult = new AuthResult(orgMsgBytes);
/*  447 */     if (authResult.isSuccess()) {
/*  448 */       if (this.authEvent != null) {
/*  449 */         this.authEvent.onAuthSuccess();
/*      */       }
/*  451 */       this.state = ProtocolStage.INITIALISATION;
/*  452 */       writeShareMsg();
/*      */     }
/*  454 */     else if (this.authEvent != null) {
/*  455 */       this.authEvent.onAuthFailed(authResult.getFailedMsg());
/*      */     } 
/*      */   }
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */   
/*      */   public void readInitialisation(byte[] orgMsgBytes) {
/*  466 */     log.debug("readInitialisation: {}", HexUtils.bytesToHexString(orgMsgBytes));
/*  467 */     InitialisationPacket initialisationPacket = new InitialisationPacket(orgMsgBytes);
/*  468 */     ImageInfo imageInfo = initialisationPacket.getImageInfo();
/*  469 */     if (this.viewerEvent != null) {
/*  470 */       this.viewerEvent.onReadImageInfo(imageInfo.getWidth(), imageInfo.getHeight());
/*      */     }
/*  472 */     this.state = ProtocolStage.NORMAL;
/*  473 */     if (this.connectEvent != null) {
/*  474 */       this.connectEvent.onAfterInitialisation();
/*      */     }
/*      */   }
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */   
/*      */   public void readNormal(byte[] orgMsgBytes) throws InvalidRFBMessageException {
/*  485 */     ReadNormalType msgType = ReadNormalType.parse(orgMsgBytes[0]);
/*  486 */     switch (msgType) {
/*      */       case FrameBufferUpdate:
/*  488 */         readFrameBufferUpdate(orgMsgBytes);
/*      */         break;
/*      */       
/*      */       case SetColourMapEntries:
/*      */       case Bell:
/*      */       case ServerCutText:
/*      */         break;
/*      */       
/*      */       case AudioBufferUpdate:
/*  497 */         readAudioBufferUpdate(orgMsgBytes);
/*      */         break;
/*      */       case VMRead:
/*  500 */         readVMRead(orgMsgBytes);
/*      */         break;
/*      */       case VMWrite:
/*  503 */         readVMWrite(orgMsgBytes);
/*      */         break;
/*      */       case VideoParam:
/*  506 */         readVideoParamRequest(orgMsgBytes);
/*      */         break;
/*      */       case KeyStatus:
/*  509 */         readKeyStatus(orgMsgBytes);
/*      */         break;
/*      */       case DeviceInfo:
/*  512 */         readDeviceInfo(orgMsgBytes);
/*      */         break;
/*      */       case AudioParam:
/*  515 */         readAudioParamRequest(orgMsgBytes);
/*      */         break;
/*      */       case MouseType:
/*  518 */         readMouseType(orgMsgBytes);
/*      */         break;
/*      */       case VideoLevel:
/*      */         break;
/*      */       case BroadcastStatus:
/*  523 */         readBroadcastRequest(orgMsgBytes);
/*      */         break;
/*      */       case BroadcastSetStatus:
/*  526 */         readBroadcastSetResult(orgMsgBytes);
/*      */         break;
/*      */       
/*      */       default:
/*  530 */         log.error("readNormal - default:{}", HexUtils.bytesToHexString(orgMsgBytes));
/*      */         break;
/*      */     } 
/*  533 */     log.trace("readNormal-{}: {}", msgType, HexUtils.bytesToHexString(orgMsgBytes));
/*      */   }
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */   
/*      */   public void readFrameBufferUpdate(byte[] orgMsgBytes) {
/*  542 */     if (orgMsgBytes.length <= 4) {
/*      */       return;
/*      */     }
/*  545 */     log.trace("session:{},readFrameBufferUpdate: {}", Long.valueOf(this.session.getId()), HexUtils.bytesToHexString(orgMsgBytes));
/*  546 */     this.videoFramePacket.parse(orgMsgBytes);
/*  547 */     if (this.videoFramePacket.resolutionIsChange && 
/*  548 */       this.viewerEvent != null) {
/*  549 */       this.viewerEvent.onChangeImageInfo(this.videoFramePacket.getImageInfo().getWidth(), this.videoFramePacket.getImageInfo().getHeight());
/*      */     }
/*      */     
/*  552 */     if (this.protocolContext.getEncodingType() == null) {
/*  553 */       this.protocolContext.setEncodingType(EncodingType.parse(this.videoFramePacket.IEncodingType));
/*      */     }
/*  555 */     this.protocolContext.setFrameFlow(this.protocolContext.getFrameFlow() + 1L);
/*  556 */     this.protocolContext.setImageInfo(this.videoFramePacket.getImageInfo());
/*      */   }
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */   
/*      */   public void readAudioBufferUpdate(byte[] orgMsgBytes) throws InvalidRFBMessageException {
/*  566 */     log.trace("readFrameBufferUpdate: {}", HexUtils.bytesToHexString(orgMsgBytes));
/*  567 */     this.audioFramePacket.parse(this.device.getDeviceTypeInt(), orgMsgBytes);
/*      */   }
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */   
/*      */   public void readDeviceInfo(byte[] orgMsgBytes) throws InvalidRFBMessageException {
/*  577 */     log.debug("readDeviceInfo: {}", HexUtils.bytesToHexString(orgMsgBytes));
/*  578 */     int length = HexUtils.bytesToIntLittle(orgMsgBytes, 4);
/*  579 */     DevicePacket device = new DevicePacket(orgMsgBytes, 8, length);
/*  580 */     if (this.deviceInfoEvent != null) {
/*  581 */       this.deviceInfoEvent.onGetDevice(device);
/*      */     }
/*      */   }
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */   
/*      */   public void readVideoParamRequest(byte[] orgMsgBytes) {
/*  591 */     log.debug("readVideoParamRequest: {}", HexUtils.bytesToHexString(orgMsgBytes));
/*  592 */     VideoParamPacket videoParamPacket = new VideoParamPacket(orgMsgBytes);
/*  593 */     if (this.viewerEvent != null) {
/*  594 */       this.viewerEvent.onVideoParam(videoParamPacket);
/*      */     }
/*      */   }
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */   
/*      */   public void readAudioParamRequest(byte[] orgMsgBytes) {
/*  604 */     log.debug("readAudioParamRequest: {}", HexUtils.bytesToHexString(orgMsgBytes));
/*  605 */     AudioParamPacket audioParamPacket = new AudioParamPacket(orgMsgBytes);
/*  606 */     if (this.viewerEvent != null) {
/*  607 */       this.viewerEvent.onAudioParam(audioParamPacket);
/*      */     }
/*      */   }
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */   
/*      */   public void readMouseType(byte[] orgMsgBytes) {
/*  617 */     log.debug("readMouseType: {}", HexUtils.bytesToHexString(orgMsgBytes));
/*  618 */     MouseTypePacket mouseTypePacket = new MouseTypePacket(orgMsgBytes);
/*  619 */     if (this.viewerEvent != null) {
/*  620 */       this.viewerEvent.onReadMouseType(mouseTypePacket);
/*      */     }
/*      */   }
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */   
/*      */   public void readKeyStatus(byte[] orgMsgBytes) {
/*  630 */     log.debug("readKeyStatus: {}", HexUtils.bytesToHexString(orgMsgBytes));
/*  631 */     KeyStatusPacket keyStatusPacket = new KeyStatusPacket(orgMsgBytes);
/*  632 */     if (this.viewerEvent != null) {
/*  633 */       this.viewerEvent.onKeyStatus(keyStatusPacket);
/*      */     }
/*      */   }
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */   
/*      */   public void readBroadcastRequest(byte[] orgMsgBytes) {
/*  643 */     log.debug("readBroadcastRequest: {}", HexUtils.bytesToHexString(orgMsgBytes));
/*  644 */     BroadcastStatusPacket broadcastStatusPacket = new BroadcastStatusPacket(orgMsgBytes);
/*  645 */     if (this.viewerEvent != null) {
/*  646 */       this.viewerEvent.onBroadcastRequest(broadcastStatusPacket);
/*      */     }
/*      */   }
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */   
/*      */   public void readBroadcastSetResult(byte[] orgMsgBytes) {
/*  656 */     log.debug("readBroadcastSet: {}", HexUtils.bytesToHexString(orgMsgBytes));
/*  657 */     BroadcastSetResultPacket broadcastSetResultPacket = new BroadcastSetResultPacket(orgMsgBytes);
/*  658 */     if (this.viewerEvent != null) {
/*  659 */       this.viewerEvent.onBroadcastSet(broadcastSetResultPacket);
/*      */     }
/*      */   }
/*      */ 
/*      */   
/*      */   public void readVMRead(byte[] orgMsgBytes) {
/*  665 */     log.debug("readVMRead: {}", HexUtils.bytesToHexString(orgMsgBytes));
/*  666 */     VMReadPacket vmReadPacket = new VMReadPacket(orgMsgBytes, this.protocolContext.getMediaType());
/*  667 */     writeVMData(vmReadPacket);
/*      */   }
/*      */   
/*      */   public void readVMWrite(byte[] orgMsgBytes) {
/*  671 */     log.debug("readVMWrite: {}", HexUtils.bytesToHexString(orgMsgBytes));
/*  672 */     if (this.vmEvent != null) {
/*  673 */       this.vmEvent.onVMWritStarting();
/*      */     }
/*  675 */     VMWritePacket vmWritePacket = new VMWritePacket(orgMsgBytes, this.protocolContext.getMediaType());
/*  676 */     this.protocolContext.setWriteByteCount(vmWritePacket.getCount() + this.protocolContext.getWriteByteCount());
/*  677 */     if (this.vmEvent != null) {
/*  678 */       this.vmEvent.onRefreshVMContext(this.protocolContext);
/*      */     }
/*      */   }
/*      */ 
/*      */   
/*      */   public void graceClose() {
/*  684 */     if (this.session == null) {
/*  685 */       log.debug("session is null, when close session");
/*      */       return;
/*      */     } 
/*  688 */     destroy();
/*  689 */     this.session.closeOnFlush();
/*      */   }
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */   
/*      */   private WriteFuture write(byte[] bytes) {
/*  698 */     if (this.session == null) {
/*  699 */       log.error("session is null, when write data");
/*  700 */       return null;
/*      */     } 
/*  702 */     log.trace("Write bytes: [{}]", HexUtils.bytesToHexString(bytes));
/*  703 */     return this.session.write(bytes);
/*      */   }
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */   
/*      */   public void writeProtocolVersion(byte[] bytes) {
/*  713 */     log.debug("writeProtocolVersion: {}", HexUtils.bytesToHexString(bytes));
/*  714 */     write(bytes);
/*      */   }
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */   
/*      */   public void writeSecurityType(byte[] type) {
/*  724 */     log.debug("writeSecurityType: {}", type);
/*  725 */     write(type);
/*      */   }
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */   
/*      */   public void writeVncAuth(byte[] bytes) {
/*  735 */     log.debug("writeVncAuth: {}", HexUtils.bytesToHexString(bytes));
/*  736 */     write(bytes);
/*      */   }
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */   
/*      */   public void writeRsaAuth(byte[] bytes) {
/*  746 */     write(bytes);
/*  747 */     log.debug("writeRsaAuth: {}", HexUtils.bytesToHexString(bytes));
/*      */   }
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */   
/*      */   public void writeShareMsg() {
/*  755 */     write(SHARE_BYTE);
/*  756 */     log.debug("writeShareMsg");
/*      */   }
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */   
/*      */   public void writeBroadCastStatusRequest() {
/*  764 */     write(BROADCAST_REQUEST);
/*  765 */     log.debug("EnginWriteBroadCastRequestMsg: {}", HexUtils.bytesToHexString(BROADCAST_REQUEST));
/*      */   }
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */   
/*      */   public void writeBroadCastSetRequest(byte[] bytes) {
/*  775 */     write(bytes);
/*  776 */     log.debug("EnginWriteSetBroadCast: {}", HexUtils.bytesToHexString(bytes));
/*      */   }
/*      */ 
/*      */   
/*      */   public void writeVMCloseRequest() {
/*  781 */     write(VM_CLOSE_REQUEST);
/*  782 */     log.debug("writeVMCloseRequest: {}", HexUtils.bytesToHexString(VM_CLOSE_REQUEST));
/*      */   }
/*      */ 
/*      */   
/*      */   public void writeVMLinkRequest() throws InvalidRFBMessageException {
/*  787 */     VMLinkPacket vmLinkPacket = new VMLinkPacket(this.protocolContext.getMediaType());
/*  788 */     if (this.vmEvent != null) {
/*  789 */       this.vmEvent.onRefreshVMContext(this.protocolContext);
/*      */     }
/*  791 */     byte[] bytes = vmLinkPacket.buildRFB();
/*  792 */     this.session.write(bytes);
/*  793 */     log.debug("writeVMRequest: {}", HexUtils.bytesToHexString(bytes));
/*      */   }
/*      */ 
/*      */   
/*      */   public void writeVMData(VMReadPacket vmReadPacket) {
/*  798 */     byte[] bytes = vmReadPacket.buildRFB();
/*  799 */     write(bytes);
/*  800 */     log.trace("writeVMData: {}", HexUtils.bytesToHexString(bytes));
/*  801 */     writeKeepAlive();
/*  802 */     this.protocolContext.setReadByteCount(vmReadPacket.getCount() + this.protocolContext.getReadByteCount());
/*  803 */     if (this.vmEvent != null) {
/*  804 */       this.vmEvent.onRefreshVMContext(this.protocolContext);
/*  805 */       this.vmEvent.onVMReadStarting();
/*      */     } 
/*      */   }
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */   
/*      */   public WriteFuture writeMouseEvent(byte[] bytes) {
/*  816 */     if (this.state == ProtocolStage.NORMAL) {
/*  817 */       log.debug("writeMouseEvent: {}", HexUtils.bytesToHexString(bytes));
/*  818 */       return write(bytes);
/*      */     } 
/*  820 */     return null;
/*      */   }
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */   
/*      */   public WriteFuture writeKeyEvent(byte[] bytes) {
/*  830 */     if (this.state == ProtocolStage.NORMAL) {
/*  831 */       log.debug("writeKeyEvent: {}", HexUtils.bytesToHexString(bytes));
/*  832 */       return write(bytes);
/*      */     } 
/*  834 */     return null;
/*      */   }
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */   
/*      */   public void writeKeepAlive() {
/*  842 */     if (this.state == ProtocolStage.NORMAL) {
/*  843 */       log.debug("writeKeepAlive: {}", HexUtils.bytesToHexString(KEEP_ALIVE_BYTES));
/*  844 */       write(KEEP_ALIVE_BYTES);
/*      */     } 
/*      */   }
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */   
/*      */   public void writeSecurityPath(byte[] bytes) {
/*  855 */     write(bytes);
/*  856 */     log.debug("writeSecurityPath: {}", HexUtils.bytesToHexString(bytes));
/*      */   }
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */   
/*      */   public void writeUserAccount(byte[] bytes) {
/*  866 */     write(bytes);
/*  867 */     log.debug("writeUserAccount: {}", HexUtils.bytesToHexString(bytes));
/*      */   }
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */   
/*      */   public void writeKeyStateParamRequest() {
/*  875 */     write(KEY_TYPE_REQUEST);
/*  876 */     log.debug("writeKeyStateParamRequest: {}", HexUtils.bytesToHexString(KEY_TYPE_REQUEST));
/*      */   }
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */   
/*      */   public void writeVideoParamRequest() {
/*  884 */     write(VIDEO_PARAM_REQUEST);
/*  885 */     log.debug("writeVideoParamRequest: {}", HexUtils.bytesToHexString(VIDEO_PARAM_REQUEST));
/*      */   }
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */   
/*      */   public void writeAudioParamRequest() {
/*  893 */     write(AUDIO_PARAM_REQUEST);
/*  894 */     log.debug("writeAudioParamRequest: {}", HexUtils.bytesToHexString(AUDIO_PARAM_REQUEST));
/*      */   }
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */   
/*      */   public void writeCustomVideoParam(VideoParamPacket videoParamPacket) {
/*  904 */     byte[] bytes = videoParamPacket.buildRFB();
/*  905 */     write(videoParamPacket.buildRFB());
/*  906 */     log.debug("writeCustomVideoParam: {}", HexUtils.bytesToHexString(bytes));
/*      */   }
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */   
/*      */   public void writeCustomAudioParam(AudioParamPacket audioParamPacket) {
/*  916 */     byte[] bytes = audioParamPacket.buildRFB();
/*  917 */     write(bytes);
/*  918 */     log.debug("writeCustomAudioParam: {}", HexUtils.bytesToHexString(bytes));
/*      */   }
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */   
/*      */   public void writeMouseTypeRequest() {
/*  926 */     write(MOUSE_TYPE_REQUEST);
/*  927 */     log.debug("writeMouseType: {}", HexUtils.bytesToHexString(MOUSE_TYPE_REQUEST));
/*      */   }
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */   
/*      */   public WriteFuture writeCustomMouseType(MouseTypePacket mouseTypePacket) {
/*  937 */     byte[] bytes = mouseTypePacket.buildRFB();
/*  938 */     WriteFuture future = write(bytes);
/*  939 */     this.viewerEvent.onWriteCustomMouseType(mouseTypePacket);
/*  940 */     log.debug("writeCustomMouseType: {}", HexUtils.bytesToHexString(bytes));
/*  941 */     return future;
/*      */   }
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */   
/*      */   public void writeKeyEvent(KeyEventPacket[] keyEventPackets) {
/*  951 */     if (this.session == null) {
/*  952 */       log.error("session == null");
/*      */     }
/*  954 */     for (KeyEventPacket keyEventPacket : keyEventPackets) {
/*  955 */       writeKeyEvent(keyEventPacket.buildRFB());
/*      */     }
/*      */   }
/*      */ 
/*      */   
/*      */   public WriteFuture writeKeyEvent(KeyEventPacket keyEventPacket) {
/*  961 */     if (this.session == null) {
/*  962 */       log.error("session == null");
/*      */     }
/*  964 */     return writeKeyEvent(keyEventPacket.buildRFB());
/*      */   }
/*      */   
/*      */   public WriteFuture writeMouseEvent(MouseEventPacket mouseEventPacket) {
/*  968 */     if (this.session == null) {
/*  969 */       log.error("session == null");
/*      */     }
/*  971 */     return writeMouseEvent(mouseEventPacket.buildRFB());
/*      */   }
/*      */ 
/*      */   
/*      */   public void writeMouseEvent(MouseEventPacket[] mouseEventPackets) {
/*  976 */     if (this.session == null) {
/*  977 */       log.error("session == null");
/*      */     }
/*  979 */     for (MouseEventPacket mouseEventPacket : mouseEventPackets) {
/*  980 */       writeMouseEvent(mouseEventPacket.buildRFB());
/*      */     }
/*      */   }
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */ 
/*      */   
/*      */   public ProtocolContext getContext() {
/*  991 */     return this.protocolContext;
/*      */   }
/*      */   
/*      */   private enum ProtocolStage {
/*  995 */     UNINITIALISED,
/*  996 */     PROTOCOL_VERSION,
/*  997 */     SECURITY_TYPES,
/*  998 */     CENTRALIZE_TYPES,
/*  999 */     SECURITY,
/* 1000 */     SECURITY_RESULT,
/* 1001 */     INITIALISATION,
/* 1002 */     NORMAL,
/* 1003 */     INVALID;
/*      */   }
/*      */ }


/* Location:              /Users/liu/Documents/工作文档/珑琪/智能盒子/kvm/svc-console-master/lib/svc-sdk-1.3.4.1/!/com/hiklife/svc/core/protocol/handler/ProtocolHandlerImpl.class
 * Java compiler version: 8 (52.0)
 * JD-Core Version:       1.1.3
 */