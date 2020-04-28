
import sys
sys.path.append("../../IoTPy/core")
sys.path.append("../../IoTPy/agent_types")
sys.path.append("../../IoTPy/helper_functions")

# stream is in IoTPy/IoTPy/core
from stream import Stream, run
# merge, map_element are in ../agent_types
from merge import zip_map
from op import map_element
# recent_values  is in ../helper_functions
from recent_values import recent_values

# This example uses map_element()
def make_echo(spoken, D, A):
    """
    Parameters
    ----------
    spoken: Stream
      The stream of the spoken or created sound.
    D: number
      The Delay
      The delay from creation of sound to hearing the
      first echo. The units of D are the number of
      points in the sound input.
    A: floating point number
      The Attenuation factor.
      The ratio of the intensity of the spoken sound
      to its first echol.

    Notes
    -----
    echo is the echo of the spoken sound
    heard is the sound that is heard; it is the spoken
    sound and its echo.

    """
    echo = Stream(name='echo', initial_value=[0]*D)
    heard = spoken + echo
    map_element(func=lambda v: v*A, in_stream=heard, out_stream=echo)
    return heard

# This example illustrates use of prepend() and f_mul().
# f_mul(heard, A) returns the stream obtained by multiplying each
# element of the stream heard by the constant A.
# prepend prepends the specified stream to in_stream to get the
# out_stream.
def make_echo_1(spoken, D, A):
    echo = Stream('echo')
    heard = spoken + echo
    prepend([0]*D, in_stream=f_mul(heard, A), out_stream=echo)
    return heard

def echo_output(input_sound, D, A):
    """
    Same as make_echo except that input_sound is a list or array
    and is not a Stream.

    """
    spoken = Stream('spoken')
    heard = make_echo(spoken, D, A)
    spoken.extend(input_sound)
    run()
    return recent_values(heard)

#-------------------------------------------------------------------
#  TESTS
#-------------------------------------------------------------------
def test_echo():
    spoken = Stream('spoken')
    heard = make_echo(spoken, D=1, A=0.5)
    spoken.extend([64, 32, 16, 8, 4, 2, 1, 0, 0, 0, 0])
    run()
    assert recent_values(heard) == [
        64.0, 64.0, 48.0, 32.0, 20.0, 12.0, 7.0, 3.5, 1.75, 0.875, 0.4375]

def test_echo_1():
    spoken = Stream('spoken')
    heard = make_echo_1(spoken, D=1, A=0.5)
    spoken.extend([64, 32, 16, 8, 4, 2, 1, 0, 0, 0, 0])
    run()
    assert recent_values(heard) == [
        64.0, 64.0, 48.0, 32.0, 20.0, 12.0, 7.0, 3.5, 1.75, 0.875, 0.4375]

def test_echo_output():
    output = echo_output(
        input_sound=[64, 32, 16, 8, 4, 2, 1, 0, 0, 0, 0],
        D=1, A=0.5)
    assert output == [
        64.0, 64.0, 48.0, 32.0, 20.0, 12.0, 7.0,
        3.5, 1.75, 0.875, 0.4375]

def test_echo_output():
    output = echo_output(
        input_sound=[64, 32, 16, 8, 4, 2, 1, 0, 0, 0, 0],
        D=1, A=0.5)
    assert output == [
        64.0, 64.0, 48.0, 32.0, 20.0, 12.0, 7.0,
        3.5, 1.75, 0.875, 0.4375]


#-------------------------------------------------
if __name__ == '__main__':
    test_echo()
    test_echo_output()
