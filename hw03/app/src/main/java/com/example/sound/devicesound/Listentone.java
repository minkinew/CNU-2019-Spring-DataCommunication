package com.example.sound.devicesound;

import android.media.AudioFormat;
import android.media.AudioRecord;
import android.media.MediaRecorder;
import android.util.Log;

import org.apache.commons.math3.complex.Complex;
import org.apache.commons.math3.transform.*;

import java.util.ArrayList;
import java.util.List;

import static com.example.sound.devicesound.ToneThread.duration;
import static java.lang.Math.abs;
import static java.lang.Math.min;
import static java.lang.Math.pow;

public class Listentone {

    int HANDSHAKE_START_HZ = 4096;
    int HANDSHAKE_END_HZ = 5120 + 1024;

    int START_HZ = 1024;
    int STEP_HZ = 256;
    int BITS = 4;

    int FEC_BYTES = 4;

    private int mAudioSource = MediaRecorder.AudioSource.MIC; //mic = alsaaudio.PCM(alsaaudio.PCM_CAPTURE, alsaaudio.PCM_NORMAL, device="default")
    private int mSampleRate = 44100; // mic.setrate(44100)
    private int mChannelCount = AudioFormat.CHANNEL_IN_MONO; //mic.setchannels(1)
    private int mAudioFormat = AudioFormat.ENCODING_PCM_16BIT; // // mic.setformat(alsaaudio.PCM_FORMAT_S16_LE)
    private float interval = 0.1f; // interval=0.1

    private int mBufferSize = AudioRecord.getMinBufferSize(mSampleRate, mChannelCount, mAudioFormat);

    public AudioRecord mAudioRecord = null;
    int audioEncodig;
    boolean startFlag;
    FastFourierTransformer transform;


    public Listentone() {
        transform = new FastFourierTransformer(DftNormalization.STANDARD);
        startFlag = false;
        mAudioRecord = new AudioRecord(mAudioSource, mSampleRate, mChannelCount, mAudioFormat, mBufferSize);
        mAudioRecord.startRecording();
    }

    private double findFrequency(double[] toTransform) { //findFrequency메소드 = dominant() function in python
        int len = toTransform.length;
        double[] real = new double[len];
        double[] img = new double[len];
        double realNum, imgNum;
        double[] mag = new double[len];
        double peak_coeff = mag[0];
        int index = 0;

        Complex[] complx = transform.transform(toTransform, TransformType.FORWARD); //복소수
        Double[] freq = this.fftfreq(complx.length, 1);

        for (int i = 0; i < complx.length; i++) {
            realNum = complx[i].getReal();
            imgNum = complx[i].getImaginary();
            mag[i] = Math.sqrt((realNum * realNum) + (imgNum * imgNum));
        }

        for (int i = 0; i < complx.length; i++) {
            if (mag[i] > peak_coeff) { //peak_coeff보다 더 크면
                peak_coeff = mag[i]; //최댓값 설정
                index = i; // 해당 인덱스 설정
            }
        }
        double peak_freq = freq[index];
        return abs(peak_freq * mSampleRate); // in Hz
    }

    private Double[] fftfreq(int length, int d) { //fftfreq 메소드(주파수 정규화)
        double val = 1.0 / (length * d);
        int results[] = new int[length];
        Double[] final_result = new Double[length];
        int N = (length - 1) / 2 + 1; // results배열의 앞부분 절반
        int M = -(length / 2); //results배열의 뒷부분 절반

        for (int i = 0; i <= N; i++) { //배열 앞부분 절반에
            results[i] = i; //0 ~ N대입
        }

        for (int i = N + 1; i < length; i++) { //배열 뒷부분 절반에
            results[i] = M; // -(n/2) ~ 0 대입
            M--;
        }
        for (int i = 0; i < length; i++) {
            final_result[i] = results[i] * val; // val를 곱해서 최종 값 구함
        }

        return final_result; //최종결과 반환
    }

    public boolean match(double freq1, double freq2) { //match메소드 = match() function in python
        return abs(freq1 - freq2) < 20;
    }

    private int findPowersize(int n) { // findPowesize메소드, buffersize의 가장 가까운 제곱수 반환
        int n_squares = 1; //2의 제곱수 변수
        while (true) {
            n_squares = n_squares * 2;
            if (n_squares >= n)
                return n_squares; //가장 가까운 제곱수 반환
        }
    }

    public List<Integer> decode_bitchunks(int chunk_bits, List<Integer> chunks) { //decode_bitchunks메소드 =  decode_bitchunks() function in python
        List<Integer> out_bytes = new ArrayList<>();
        int next_read_chunk = 0;
        int next_read_bit = 0;
        int byte_ = 0;
        int bits_left = 8;

        while (next_read_chunk < chunks.size()) {
            int can_fill = chunk_bits - next_read_bit;
            int to_fill = min(bits_left, can_fill);
            int offset = chunk_bits - next_read_bit - to_fill;
            byte_ <<= to_fill;
            int shifted = chunks.get(next_read_chunk) & (((1 << to_fill) - 1) << offset);
            byte_ |= shifted >> offset;
            bits_left -= to_fill;
            next_read_bit += to_fill;

            if (bits_left <= 0) { //if bits_left <= 0:
                out_bytes.add(byte_);
                byte_ = 0;
                bits_left = 8;
            }
            if (next_read_bit >= chunk_bits) { //if next_read_bit >= chunk_bits:
                next_read_chunk += 1;
                next_read_bit -= chunk_bits;
            }
        }
        return out_bytes;
    }

    public List<Integer> extract_packet(List<Double> freqs) { //extract_packet메소드 = extract_packet() function in python
        List<Double> half_freq = new ArrayList<>();
        List<Integer> bit_chunks = new ArrayList<>();
        List<Integer> bit_chunks2 = new ArrayList<>();

        for (int i = 0; i < freqs.size(); i++) {
            half_freq.add(freqs.get(i));
        }

        for (int i = 0; i < half_freq.size(); i++) { //bit_chunks = [int(round((f - START_HZ) / STEP_HZ)) for f in freqs]
            bit_chunks.add((int) Math.round((half_freq.get(i) - START_HZ) / STEP_HZ));
        }

        for (int i = 1; i < bit_chunks.size(); i++) { // bit_chunks = [c for c in bit_chunks[1:] if 0 <= c < (2 ** BITS)]
            if (bit_chunks.get(i) >= 0 && bit_chunks.get(i) < pow(2, BITS)) {
                bit_chunks2.add(bit_chunks.get(i));
            }
        }
        List<Integer> bits = decode_bitchunks(BITS, bit_chunks2);
        return bits;
    }

    public void PreRequest() { //PreRequest메소드 = listen_linux() function in python
        //recorder로부터 음성을 읽는 부분, buffer에 소리데이터가 들어가게 되어 buffer를 이용해 fft를 함.
        int blocksize = findPowersize((int) (long) Math.round(interval / 2 * mSampleRate));
        short[] buffer = new short[blocksize]; //chuck
        double[] trans = new double[blocksize]; // chuck = buffer -> trans
        List<Double> packet = new ArrayList<>();
        List<Integer> byte_stream = new ArrayList<>();

        while (true) {
            int bufferedReadResult = mAudioRecord.read(buffer, 0, blocksize);
            if (bufferedReadResult < 0) //if not l: continue
                continue;
            for (int i = 0; i < blocksize; i++) //chunk =np.fromstring(data, dtype = np.int16)
                trans[i] = buffer[i];

            double dom = findFrequency(trans); // dom = dominant(frame_rate, chunk); 소리를 주파수로 변환, 소리에 맞게 분리

            if (startFlag && match(dom, HANDSHAKE_END_HZ)) { //끝 주파수를 수신함
                byte_stream = extract_packet(packet); //주파수의 묶음을 데이터로 바꿔줌(extract packet)

                String result = "";
                for (int index = 0; index < byte_stream.size(); index++) {
                    result = result + Character.toString((char) ((int) byte_stream.get(index)));
                }

                Log.d("RESULT_DATA : ", result); //result값 출력
                packet.clear();
                startFlag = false;
            } else if (startFlag)
                packet.add(dom);  //packet.append(dom)
            else if (match(dom, HANDSHAKE_START_HZ))
                startFlag = true; //in_packet = True
            Log.d("dom", "" + dom);
        }
    }
}
