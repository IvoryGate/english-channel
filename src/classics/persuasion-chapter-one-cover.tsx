import {AbsoluteFill, Img, staticFile} from 'remotion';

const serif = 'Georgia, Times New Roman, serif';

export const PersuasionChapterOneCover = () => (
  <AbsoluteFill style={{backgroundColor: '#f3dfb7', color: '#4c3328', overflow: 'hidden'}}>
    <Img src={staticFile('classics/persuasion/chapter-01-cover-bg-v2.png')} style={{position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'cover'}} />
    <AbsoluteFill style={{background: 'linear-gradient(90deg, rgba(255,249,232,.91) 0%, rgba(255,246,222,.72) 38%, rgba(255,246,222,.05) 62%, rgba(87,55,34,.08) 100%)'}} />
    <div style={{position: 'absolute', inset: 48, border: '3px solid rgba(169,119,46,.75)'}} />
    <div style={{position: 'absolute', inset: 65, border: '1px solid rgba(169,119,46,.40)'}} />
    <div style={{position: 'absolute', left: 126, top: 110, width: 1020}}>
      <div style={{fontFamily: serif, fontSize: 31, letterSpacing: 13, color: '#a87332', fontWeight: 700}}>JANE AUSTEN'S</div>
      <div style={{fontFamily: serif, fontSize: 150, lineHeight: .92, letterSpacing: 3, fontWeight: 700, marginTop: 42, textShadow: '0 2px 0 rgba(255,255,255,.8)'}}>PERSUASION</div>
      <div style={{width: 170, height: 4, background: '#b78636', margin: '42px 0'}} />
      <div style={{fontFamily: serif, fontSize: 82, lineHeight: 1.04, fontWeight: 700, letterSpacing: 1}}>A FAMILY<br />OF PRIDE</div>
      <div style={{fontFamily: serif, fontSize: 31, lineHeight: 1.35, fontStyle: 'italic', color: '#76584b', marginTop: 22}}>At Kellynch Hall, appearances are everything.</div>
      <div style={{display: 'flex', gap: 24, alignItems: 'center', marginTop: 58}}>
        <div style={{fontFamily: serif, fontSize: 34, letterSpacing: 7, border: '2px solid #b78636', padding: '15px 22px', color: '#4c3328', background: 'rgba(255,252,242,.65)'}}>CHAPTER 1</div>
        <div style={{fontFamily: serif, fontSize: 34, letterSpacing: 7, background: '#c9877e', padding: '17px 24px', color: '#fff9eb', fontWeight: 700}}>FULL AUDIOBOOK</div>
      </div>
      <div style={{fontFamily: serif, fontSize: 29, letterSpacing: 8, marginTop: 42, color: '#6f5043', fontWeight: 700}}>ENGLISH LISTENING ROOM</div>
    </div>
  </AbsoluteFill>
);
