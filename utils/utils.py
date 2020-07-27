
import numpy as np
import matplotlib.pyplot as plt


def get_MAC_id_from_bytes(high_byte, low_byte):
    return f"{high_byte:02X}:{low_byte:02X}"


def get_word_from_bytes(high_byte, low_byte):
    # print(high_byte, low_byte)
    return (high_byte << 8) | low_byte


def get_int_from_bytes(highest_byte, higher_byte, high_byte, low_byte):
    return (highest_byte << 24) | (higher_byte << 16) | (high_byte << 8) | low_byte


def get_bytes_from_int(this_int):
    B1 = (this_int & 0xFF000000) >> 24
    B2 = (this_int & 0x00FF0000) >> 16
    B3 = (this_int & 0x0000FF00) >> 8
    B4 = (this_int & 0x000000FF)
    return B1, B2, B3, B4


def calc_half_wave_RMS():
    frequency = 50
    SIGNAL_AMPLITUDE = 120  # this is ADC raw sample sine wave, that's why!!!
    noise_amplitude = 0
    num_samples = 400
    delay_time = 100e-6
    SENSOR_RATING = 30
    time = np.linspace(0, delay_time*num_samples, num_samples)
    noise = noise_amplitude * np.random.randn(num_samples)
    full_ADC_wave = SIGNAL_AMPLITUDE * np.sin(2 * np.pi * frequency * time) + noise
    half_ADC_wave = np.zeros_like(full_ADC_wave)
    half_ADC_wave[:] = full_ADC_wave
    half_ADC_wave[half_ADC_wave < 0] = 0  # rectify the current wave
    True_RMS_current_value = SENSOR_RATING / 723.18 * 1/0.707 * np.sqrt(np.sum(np.square(half_ADC_wave), axis=0) / num_samples)
    MAX_SAMPLE_RMS_current_value = SENSOR_RATING / 724.07 * np.max(half_ADC_wave, axis=0)
    # find the zero crossings
    non_zeroes_sum = 0
    non_zeroes_count = 0
    for i in range(num_samples):
        this_current_value = half_ADC_wave[i]
        if this_current_value > 0:
            non_zeroes_sum += this_current_value
            non_zeroes_count += 1
            pass
        pass
    AVERAGE_SAMPLE_RMS_current_value = SENSOR_RATING / 718.89 * 1.1 * non_zeroes_sum/non_zeroes_count
    print(">> True RMS Value: {:0.2f}".format(True_RMS_current_value))
    print(">> MAX_SAMPLE-Based RMS Value: {:0.2f}".format(MAX_SAMPLE_RMS_current_value))
    print(">> AVG_SAMPLE-Based RMS Value: {:0.2f}".format(AVERAGE_SAMPLE_RMS_current_value))
    plt.plot(time, half_ADC_wave)
    plt.show()
    pass


if __name__ == '__main__':
    calc_half_wave_RMS()
