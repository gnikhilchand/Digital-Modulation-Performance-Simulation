import numpy as np
import matplotlib.pyplot as plt
from scipy.special import erfc

# --- Simulation Parameters ---
NUM_BITS = 10**6  # Number of bits to simulate
EbN0_dB_range = np.arange(0, 15, 1)  # Eb/N0 range in dB for simulation
MODULATION_SCHEMES = ['BPSK', 'QPSK', '16-QAM']

# --- Main Simulation Function ---
def simulate_ber():
    """
    Main function to simulate BER for BPSK, QPSK, and 16-QAM.
    """
    ber_results = {scheme: [] for scheme in MODULATION_SCHEMES}
    theoretical_ber = {scheme: [] for scheme in MODULATION_SCHEMES}

    for EbN0_dB in EbN0_dB_range:
        print(f"Simulating for Eb/N0 = {EbN0_dB} dB")

        # Convert Eb/N0 from dB to linear scale
        EbN0_linear = 10**(EbN0_dB / 10.0)

        # --- Generate random bits ---
        transmitted_bits = np.random.randint(0, 2, NUM_BITS)

        for scheme in MODULATION_SCHEMES:
            # --- Modulation ---
            if scheme == 'BPSK':
                k = 1
                # Map bits: 0 -> +1, 1 -> -1
                transmitted_symbols = 2 * transmitted_bits - 1
            elif scheme == 'QPSK':
                k = 2
                # Reshape bits into pairs and map to complex symbols
                # 00->(1+j)/sqrt(2), 01->(-1+j)/sqrt(2), 10->(1-j)/sqrt(2), 11->(-1-j)/sqrt(2)
                transmitted_symbols = (1 - 2 * transmitted_bits[0::2]) + 1j * (1 - 2 * transmitted_bits[1::2])
                transmitted_symbols /= np.sqrt(2) # Normalize symbol energy to 1
            elif scheme == '16-QAM':
                k = 4
                # Mapping from 4 bits to a 16-QAM constellation point
                mapping = {
                    (0,0,0,0) : -3-3j, (0,0,0,1) : -3-1j, (0,0,1,0) : -3+3j, (0,0,1,1) : -3+1j,
                    (0,1,0,0) : -1-3j, (0,1,0,1) : -1-1j, (0,1,1,0) : -1+3j, (0,1,1,1) : -1+1j,
                    (1,0,0,0) :  3-3j, (1,0,0,1) :  3-1j, (1,0,1,0) :  3+3j, (1,0,1,1) :  3+1j,
                    (1,1,0,0) :  1-3j, (1,1,0,1) :  1-1j, (1,1,1,0) :  1+3j, (1,1,1,1) :  1+1j
                }
                bits_reshaped = transmitted_bits.reshape(-1, k)
                transmitted_symbols = np.array([mapping[tuple(b)] for b in bits_reshaped])
                transmitted_symbols /= np.sqrt(10) # Normalize average symbol energy to 1

            # --- Channel: Additive White Gaussian Noise (AWGN) ---
            # Calculate noise variance (sigma^2)
            # Es/N0 = k * Eb/N0
            # Noise variance is N0/2 for each dimension (real and imaginary)
            EsN0_linear = k * EbN0_linear
            noise_variance = 1 / (2 * EsN0_linear)
            
            # Generate complex Gaussian noise
            noise = np.sqrt(noise_variance) * (np.random.randn(len(transmitted_symbols)) + 1j * np.random.randn(len(transmitted_symbols)))
            received_symbols = transmitted_symbols + noise

            # --- Demodulation ---
            received_bits = []
            if scheme == 'BPSK':
                # Decision rule: if real part > 0, decide bit 0, else bit 1
                received_bits = (np.real(received_symbols) < 0).astype(int)
            elif scheme == 'QPSK':
                # Decision rule based on quadrant
                bits_real = (np.real(received_symbols) < 0).astype(int)
                bits_imag = (np.imag(received_symbols) < 0).astype(int)
                received_bits = np.empty(transmitted_bits.shape, dtype=int)
                received_bits[0::2] = bits_real
                received_bits[1::2] = bits_imag
            elif scheme == '16-QAM':
                # Minimum distance decoding
                constellation = np.array(list(mapping.values())) / np.sqrt(10)
                demapping = {v: k for k, v in mapping.items()}

                for s in received_symbols:
                    distances = np.abs(s - constellation)
                    closest_point = constellation[np.argmin(distances)]
                    received_bits.extend(demapping[closest_point * np.sqrt(10)])

            # --- BER Calculation ---
            num_errors = np.sum(transmitted_bits != received_bits)
            ber = num_errors / NUM_BITS
            ber_results[scheme].append(ber)

        # --- Theoretical BER Calculation ---
        theoretical_ber['BPSK'].append(0.5 * erfc(np.sqrt(EbN0_linear)))
        theoretical_ber['QPSK'].append(0.5 * erfc(np.sqrt(EbN0_linear))) # Same as BPSK for Gray coding
        # Approximation for 16-QAM BER
        theoretical_ber['16-QAM'].append((3/8) * erfc(np.sqrt( (4/10) * EbN0_linear)))

    return ber_results, theoretical_ber


# --- Plotting ---
def plot_results(sim_ber, theory_ber):
    """
    Plots the simulated and theoretical BER results.
    """
    plt.figure(figsize=(10, 7))
    
    for scheme in MODULATION_SCHEMES:
        plt.semilogy(EbN0_dB_range, sim_ber[scheme], 'o', label=f'Simulated {scheme}')
        plt.semilogy(EbN0_dB_range, theory_ber[scheme], '-', label=f'Theoretical {scheme}')

    plt.grid(True, which='both')
    plt.xlabel('$E_b/N_0$ (dB)')
    plt.ylabel('Bit Error Rate (BER)')
    plt.title('BER Performance of Digital Modulation Schemes in AWGN Channel')
    plt.legend()
    plt.ylim([10**-5, 1])
    plt.show()


# --- Main execution ---
if __name__ == '__main__':
    simulated_ber_results, theoretical_ber_results = simulate_ber()
    plot_results(simulated_ber_results, theoretical_ber_results)