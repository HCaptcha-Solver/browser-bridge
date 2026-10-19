import test from 'node:test';
import assert from 'node:assert/strict';
import {samePixels, selectedAnimation, staticSamples, temporalSnapshot} from '../javascript/capture.mjs';

function samples(){return Array.from({length:8},(_,phase)=>{
 const sample=Array.from({length:10000},()=>[230,230,230]);
 for(let y=40;y<49;y++)for(let x=40;x<49;x++)sample[y*100+x]=[100+phase%2*50,80,70];
 return {question:'Click the circle',canvases:[{x:0,y:100,width:1000,height:800}],tiles:[],references:[],prompt:null,
  box:{width:520,height:570},sample,image:String(phase)};
});}
test('animation only permits observed positions and holds out two frames',()=>{
 const frames=samples(), learned=temporalSnapshot(frames);
 assert.equal(staticSamples(frames),false);assert.ok(learned && learned.temporal_frames.length<=5);
 const next=structuredClone(frames[0]);next.sample[4444]=[240,150,190];
 assert.equal(samePixels(learned,next),true);
 next.sample[8080]=[0,0,0];assert.equal(samePixels(learned,next),false);
 assert.equal(temporalSnapshot([...frames.slice(0,-1),next]),null);
});
test('whole scene changes and new questions cannot form an animation mask',()=>{
 let frames=samples();frames[1].sample=Array.from({length:10000},()=>[0,0,0]);
 assert.equal(temporalSnapshot(frames),null);
 frames=samples();frames.at(-1).question='Click a different animal';assert.equal(temporalSnapshot(frames),null);
});
test('selected marker anchors only known clicks and never expands the animation mask',()=>{
 const frames=samples(), learned=temporalSnapshot(frames), after=structuredClone(frames.at(-1));
 after.sample[4453]=[0,0,240];assert.equal(samePixels(learned,after),false);
 assert.equal(samePixels(learned,after,[[440,440]]),true);
 const selected=selectedAnimation(learned,after,[[440,440]],[]);
 assert.equal(samePixels(selected,after),true);assert.deepEqual(selected.animation.moving,learned.animation.moving);
 const changed=structuredClone(after);changed.sample[8080]=[0,0,0];assert.equal(samePixels(selected,changed),false);
});
