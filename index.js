const video = document.querySelector('#video')
const start = document.querySelector('.start-btn')
const end = document.querySelector('.end-btn')
const statusText = document.querySelector('#status')
const stateText = document.querySelector('#state')

var pc = null

const createPeerConnection = () => {
  let config = {
    sdpSemantics: 'unified-plan',
    // iceServers: [{ urls: ['stun:stun.l.google.com:19302'] }],
  }

  pc = new RTCPeerConnection()

  pc.ontrack = (evt) => {
    console.log('tracking')
    console.log(evt)
    if (evt.track.kind == 'video') {
      video.srcObject = evt.streams[0]
      console.log('play vioe')
    } else {
      video.srcObject = evt.streams[0]
    }
  }

  pc.oniceconnectionstatechange = (e) => {
    statusText.textContent = `${pc.iceConnectionState}`
  }

  pc.onicegatheringstatechange = () => {
    let label = 'Unknown'

    switch (pc.iceGatheringState) {
      case 'new':
      case 'complete':
        label = 'Idle'
        break
      case 'gathering':
        label = 'Determining route'
        break
    }

    stateText.textContent = `${pc.iceGatheringState}`
  }

  return pc
}

const negotiate = async () => {
  pc.addTransceiver('video', { direction: 'recvonly' })
  pc.addTransceiver('audio', { direction: 'recvonly' })

  const offer = await pc.createOffer()

  await pc.setLocalDescription(offer)
  const response = await fetch('/offer', {
    body: JSON.stringify({
      sdp: offer.sdp,
      type: offer.type,
    }),
    headers: {
      'Content-Type': 'application/json',
    },
    method: 'POST',
  })

  try {
    const answer = await response.json()
    console.log(answer)
    await pc.setRemoteDescription(answer)
  } catch (error) {
    console.log(error)
  }
}

const startConn = async (e) => {
  console.log('start connection')
  pc = createPeerConnection()

  start.disabled = true
  await negotiate()
  end.disabled = false
}

const endConn = (e) => {
  console.log('end connection')
  end.disabled = true
  pc.close()
  start.disabled = false
}

start.addEventListener('click', startConn)
end.addEventListener('click', endConn)
