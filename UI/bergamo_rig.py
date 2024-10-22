from datetime import date, datetime, timezone
from aind_data_schema_models.modalities import Modality
import aind_data_schema.components.devices as d
import aind_data_schema.core.rig as r
import sys

def generate_rig_json():
    rig = r.Rig(
        rig_id="Bergamo_2p-photostim-room442_20241021",
        modification_date=date(2022, 1, 1),
        modalities=[Modality.POPHYS, Modality.BEHAVIOR, Modality.BEHAVIOR_VIDEOS],  
        daqs = [d.DAQDevice(name = 'PXI',
               manufacturer = d.Organization.NATIONAL_INSTRUMENTS,
               data_interface = 'PXI',
               computer_name = '2p_PC')],
        cameras=[
            d.CameraAssembly(
                name="Side Face Camera Assembly",
                camera_target=d.CameraTarget.SIDE,
                camera=d.Camera(
                    name="Side Face Camera",
                    detector_type="Camera",
                    serial_number="19414825",
                    manufacturer=d.Organization.FLIR,
                    model="Blackfly S BFS-U3-16S2M",
                    notes="",
                    data_interface="USB",
                    computer_name="",
                    #max_frame_rate=226,
                    sensor_width=1440,
                    sensor_height=1080,
                    crop_width=900,
                    crop_height=500,
                    chroma="Monochrome",
                    cooling="Air",
                    bin_mode="Additive",
                    recording_software=d.Software(name="pyBpod",
                                                    version="26140c2",  
                                                    url="https://github.com/rozmar/pySpinCapture",),
                ),
                lens=d.Lens(
                    name="Side Camera Lens",
                    model="Tamron 12VM412ASIR",
                    serial_number="unknown",
                    manufacturer=d.Organization.OTHER,
                    max_aperture="f/1.2",
                    notes='Focal Length 4-12mm 1/2" IR F/1.2',
                ),
                filter= d.Filter(
                    name="LP filter",
                    filter_type="Short pass",
                    manufacturer=d.Organization.THORLABS,
                    description="850 nm shortpass filter",
    )
            ),
            d.CameraAssembly(
                name="Bottom Face Camera Assembly",
                camera_target=d.CameraTarget.BOTTOM,
                camera=d.Camera(
                    name="Bottom Face Camera",
                    detector_type="Camera",
                    serial_number="1944074",
                    manufacturer=d.Organization.FLIR,
                    model="Blackfly S BFS-U3-16S2M",
                    notes="",
                    data_interface="USB",
                    computer_name="",
                    #max_frame_rate=226,
                    sensor_width=1440,
                    sensor_height=1080,
                    crop_width=900,
                    crop_height=500,
                    chroma="Monochrome",
                    cooling="Air",
                    bin_mode="Additive",
                    recording_software=d.Software(name="pyBpod",
                                                    version="26140c2",  
                                                    url="https://github.com/rozmar/pySpinCapture",),
                ),
                lens=d.Lens(
                    name="Bottom Camera Lens",
                    model="Tamron 12VM412ASIR",
                    serial_number="unknown",
                    manufacturer=d.Organization.OTHER,
                    max_aperture="f/1.2",
                    notes='FocFF562-Di03-25x36al Length 4-12mm 1/2" IR F/1.2',
                ),
            ),
        ],
        detectors=[
            d.Detector(
                name="Red PMT",
                serial_number="AF7695",
                manufacturer=d.Organization.THORLABS,
                model="PMT2101",
                detector_type="Photomultiplier Tube",
                data_interface="PXI",
                cooling="Air",
            ),
            d.Detector(
                name="Green PMT",
                serial_number="AF7690",
                manufacturer=d.Organization.THORLABS,
                model="PMT2101",
                detector_type="Photomultiplier Tube",
                data_interface="PXI",
                cooling="Air",
            ),
        ],
        light_sources=[
            d.Laser(
                name="Monaco Laser",
                manufacturer=d.Organization.COHERENT_SCIENTIFIC,
                model="Monaco",
                serial_number="0918012925",
                wavelength=1035,
                maximum_power=40000,
                coupling="Free-space",
            ),
            d.Laser(
                name="Chameleon Laser",
                manufacturer=d.Organization.COHERENT_SCIENTIFIC,
                model="Chameleon",
                serial_number="GDP.1185374.8460",
                wavelength=920,
                maximum_power=1500,
                coupling="Free-space",
            ),
        ],
        mouse_platform=d.Tube(
            name="Standard Mouse Tube",
            diameter=3.0,  # Add the required diameter field
            notes="Mouse sits in a plastic tube",
        ),
        objectives=[
            d.Objective(
                name="16x Objective",
                serial_number="none",
                manufacturer=d.Organization.NIKON,
                model="N16XLWD-PF - 16X Nikon CFI LWD Plan Fluorite Objective",
                numerical_aperture=0.8,
                magnification=16,
                immersion="water",
                notes = '3.0 mm WD'
            )
        ],
        calibrations=[
            d.Calibration(
                calibration_date=datetime(2022, 1, 4, tzinfo=timezone.utc),
                device_name="Monaco Laser",
                description="Laser Power Calibration",
                input={"power_setting": []},
                output={"power_output": []},
                notes="Calibration of the laser power output at different settings"
            ),
            d.Calibration(
                calibration_date=datetime(2022, 1, 4, tzinfo=timezone.utc),
                device_name="Chameleon Laser",
                description="Laser Power Calibration",
                input={"power_setting": [0,	5,	10,	15,	20,	40,	60,	80,	100]},
                output={"power_output": [1,	13,	30,	50,	67,	140,	213,	280,	340]},
                notes="Calibration of the laser power output at different settings"
            )
        ],
        filters=[
            d.Filter(
                name="Green emission filter",
                manufacturer=d.Organization.SEMROCK,
                model="FF03-525/50-25",
                filter_type="Band pass",
                center_wavelength=525,
                diameter=25,
            ),
            d.Filter(
                name="Red emission filter",
                manufacturer=d.Organization.CHROMA,
                model="ET620/60m",
                filter_type="Band pass",
                center_wavelength=620,
                diameter=25,
            ),
            d.Filter(
                name="Emission dichroic",
                model="FF562-Di03-25x36",
                manufacturer=d.Organization.SEMROCK,
                filter_type="Dichroic",
                height=25,
                width=36,
                cut_off_wavelength=562,)
                ],
        stimulus_devices=[
            d.Speaker(name='speaker',
                      manufacturer=d.Organization.OTHER),
            d.RewardDelivery(
                 reward_spouts=[d.RewardSpout(name='Lickport',
                                              lick_sensor=d.Device(name="Janelia_Lick_Detector",
                                                                    device_type="Lick detector",
                                                                    manufacturer=d.Organization.JANELIA,
                                                                ),
                                             side='Center',
                                             spout_diameter=1.3,
                                             solenoid_valve=d.Device(device_type="Solenoid", name="Solenoid"))])
            
        ]
    )
    
    # Serialize to JSON
    json_data = rig.model_dump_json()
    return json_data



#missing stuff: reward valve info, additional devices Bergamo thorlabs and model
#Future: add position of cameras